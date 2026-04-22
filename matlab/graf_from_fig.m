function g = graf_from_fig(fig)
% GRAF_FROM_FIG  Extract a GrAF struct from a MATLAB figure handle.
%
%   g = graf_from_fig(fig)
%   g = graf_from_fig()          % uses gcf
%
%   Returns a struct compatible with graf_save / graf_load / graf_to_fig.
%   Supports: line plots, scatter, error bars, pcolor/surf surfaces.

    if nargin < 1 || isempty(fig)
        fig = gcf;
    end

    g = struct();
    g.supertitle = '';

    % Try to extract sgtitle text
    st = findobj(fig, 'Type', 'text', '-and', 'Tag', 'sgtitle');
    if ~isempty(st)
        g.supertitle = st(1).String;
    end

    % Figure size in cm
    fig.Units = 'inches';
    sz = fig.Position;
    cm_per_inch = 2.54;
    g.fig_width_cm  = sz(3) * cm_per_inch;
    g.fig_height_cm = sz(4) * cm_per_inch;

    % Find all non-legend axes
    all_axes = findobj(fig, 'Type', 'axes');
    all_axes = all_axes(~arrayfun(@(a) isa(a, 'matlab.graphics.illustration.Legend'), all_axes));
    % Reverse so Ax0 is top-left
    all_axes = flipud(all_axes);

    n_axes = numel(all_axes);
    g.axes = struct();

    % Determine subplot grid
    [nrows, ncols] = detect_grid(fig, all_axes);

    for ai = 1:n_axes
        ax_h    = all_axes(ai);
        ax_name = sprintf('Ax%d', ai - 1);
        ax_s    = extract_axis(ax_h, nrows, ncols, ai, n_axes);
        g.axes.(ax_name) = ax_s;
    end
end

% ---------------------------------------------------------------------------
% Axis extraction
% ---------------------------------------------------------------------------
function ax_s = extract_axis(ax_h, nrows, ncols, ai, n_axes)
    ax_s = struct();

    ax_s.title  = char(ax_h.Title.String);
    ax_s.grid_on = strcmp(ax_h.XGrid, 'on');

    % Position / span (1-based row, col)
    [r, c] = idx_to_rc(ai, ncols);
    ax_s.position = [r; c];
    ax_s.span     = [1; 1];

    % Determine axis type from contents
    has_surf = ~isempty(findobj(ax_h, 'Type', 'patch')) || ~isempty(findobj(ax_h, 'Type', 'surface'));
    is_3d    = ~isempty(findobj(ax_h, 'Type', 'line', '-and', '-function', @(o) ~isempty(o.ZData)));

    if has_surf
        ax_s.axis_type = 'AXIS_SURFACE';
    elseif is_3d || ~isempty(findobj(ax_h, 'Type', 'line', '-and', '-function', @(o) numel(o.ZData) > 0))
        ax_s.axis_type = 'AXIS_LINE3D';
    else
        ax_s.axis_type = 'AXIS_LINE2D';
    end

    % Axes scales
    ax_s.x_axis   = extract_scale(ax_h, 'x');
    ax_s.y_axis_L = extract_scale(ax_h, 'y');
    ax_s.y_axis_R = empty_scale();
    ax_s.z_axis   = extract_scale(ax_h, 'z');

    % Traces
    ax_s.traces   = struct();
    ax_s.surfaces = struct();

    lines_all   = findobj(ax_h, 'Type', 'line');
    errbar_objs = findobj(ax_h, 'Type', 'ErrorBar');

    tr_idx = 0;

    % Error bars (MATLAB ErrorBar objects)
    for ei = 1:numel(errbar_objs)
        eb = errbar_objs(ei);
        tr = extract_errorbar(eb);
        ax_s.traces.(sprintf('Tr%d', tr_idx)) = tr;
        tr_idx = tr_idx + 1;
    end

    % Plain lines (skip those that are part of an errorbar)
    eb_line_tags = {};
    for ei = 1:numel(errbar_objs)
        eb_line_tags{end+1} = errbar_objs(ei).Tag;
    end

    for li = 1:numel(lines_all)
        ln = lines_all(li);
        % Skip child lines of errorbar containers
        if isa(ln.Parent, 'matlab.graphics.chart.primitive.ErrorBar')
            continue;
        end
        z_vals = ln.ZData;
        if isempty(z_vals) || all(z_vals == 0)
            tr = extract_line2d(ln);
        else
            tr = extract_line3d(ln);
        end
        ax_s.traces.(sprintf('Tr%d', tr_idx)) = tr;
        tr_idx = tr_idx + 1;
    end

    % Surfaces (pcolor, surf)
    surf_objs = [findobj(ax_h, 'Type', 'surface'); findobj(ax_h, 'Type', 'patch')];
    sf_idx = 0;
    for si = 1:numel(surf_objs)
        sf = extract_surface(surf_objs(si), ax_h);
        ax_s.surfaces.(sprintf('Sf%d', sf_idx)) = sf;
        sf_idx = sf_idx + 1;
    end
end

% ---------------------------------------------------------------------------
% Scale
% ---------------------------------------------------------------------------
function sc = extract_scale(ax_h, which_axis)
    sc = struct();
    switch which_axis
        case 'x'
            sc.label    = char(ax_h.XLabel.String);
            lim         = ax_h.XLim;
            ticks       = ax_h.XTick;
            tick_labels = ax_h.XTickLabel;
            sc.is_valid = true;
        case 'y'
            sc.label    = char(ax_h.YLabel.String);
            lim         = ax_h.YLim;
            ticks       = ax_h.YTick;
            tick_labels = ax_h.YTickLabel;
            sc.is_valid = true;
        case 'z'
            try
                sc.label    = char(ax_h.ZLabel.String);
                lim         = ax_h.ZLim;
                ticks       = ax_h.ZTick;
                tick_labels = ax_h.ZTickLabel;
                sc.is_valid = true;
            catch
                sc = empty_scale();
                return;
            end
    end
    sc.val_min = lim(1);
    sc.val_max = lim(2);
    sc.tick_list = ticks(:)';
    if ischar(tick_labels)
        sc.tick_label_list = {tick_labels};
    elseif iscell(tick_labels)
        sc.tick_label_list = tick_labels;
    else
        sc.tick_label_list = {};
    end
    sc.minor_tick_list = [];
end

function sc = empty_scale()
    sc = struct();
    sc.is_valid = false;
    sc.label    = '';
    sc.val_min  = 0.0;
    sc.val_max  = 1.0;
    sc.tick_list = [];
    sc.tick_label_list = {};
    sc.minor_tick_list = [];
end

% ---------------------------------------------------------------------------
% Trace extraction
% ---------------------------------------------------------------------------
function tr = extract_line2d(ln)
    tr = struct();
    tr.trace_type   = 'TRACE_LINE2D';
    tr.display_name = char(ln.DisplayName);
    tr.x_data       = double(ln.XData(:));
    tr.y_data       = double(ln.YData(:));
    tr.z_data       = [];

    tr.line_type  = ln.LineStyle;
    tr.line_width = ln.LineWidth;
    col           = ln.Color;
    tr.line_color = col(1:3);

    tr.marker_type  = matlab_marker_to_graf(ln.Marker);
    tr.marker_size  = ln.MarkerSize;
    mfc = ln.MarkerFaceColor;
    if ischar(mfc)
        tr.marker_color = tr.line_color;
    else
        tr.marker_color = double(mfc(1:3));
    end

    tr.alpha       = 1.0;
    tr.use_yaxis_R = false;

    tr = add_empty_errbar_fields(tr);
end

function tr = extract_line3d(ln)
    tr = extract_line2d(ln);
    tr.trace_type = 'TRACE_LINE3D';
    tr.z_data     = double(ln.ZData(:));
end

function tr = extract_errorbar(eb)
    tr = struct();
    tr.trace_type   = 'TRACE_LINE2D';
    tr.display_name = char(eb.DisplayName);
    tr.x_data       = double(eb.XData(:));
    tr.y_data       = double(eb.YData(:));
    tr.z_data       = [];

    tr.line_type  = eb.LineStyle;
    tr.line_width = eb.LineWidth;
    col = eb.Color;
    tr.line_color = col(1:3);

    tr.marker_type  = matlab_marker_to_graf(eb.Marker);
    tr.marker_size  = eb.MarkerSize;
    mfc = eb.MarkerFaceColor;
    if ischar(mfc)
        tr.marker_color = tr.line_color;
    else
        tr.marker_color = double(mfc(1:3));
    end

    tr.alpha       = 1.0;
    tr.use_yaxis_R = false;

    tr.has_error_bars = true;

    n = numel(tr.x_data);
    if ~isempty(eb.YNegativeDelta)
        tr.y_err_neg = abs(double(eb.YNegativeDelta(:)));
    else
        tr.y_err_neg = zeros(n, 1);
    end
    if ~isempty(eb.YPositiveDelta)
        tr.y_err_pos = abs(double(eb.YPositiveDelta(:)));
    else
        tr.y_err_pos = zeros(n, 1);
    end
    if ~isempty(eb.XNegativeDelta)
        tr.x_err_neg = abs(double(eb.XNegativeDelta(:)));
    else
        tr.x_err_neg = zeros(n, 1);
    end
    if ~isempty(eb.XPositiveDelta)
        tr.x_err_pos = abs(double(eb.XPositiveDelta(:)));
    else
        tr.x_err_pos = zeros(n, 1);
    end

    ecol = eb.Color;
    tr.err_line_color = ecol(1:3);
    tr.err_cap_color  = ecol(1:3);
    tr.err_line_width = eb.LineWidth;
    tr.err_cap_width  = eb.LineWidth;
    tr.err_cap_size   = eb.CapSize / 2;   % match Python factor-of-2
    tr.err_cap_visible = true;
end

function tr = add_empty_errbar_fields(tr)
    n = numel(tr.x_data);
    tr.has_error_bars  = false;
    tr.x_err_neg       = zeros(n, 1);
    tr.x_err_pos       = zeros(n, 1);
    tr.y_err_neg       = zeros(n, 1);
    tr.y_err_pos       = zeros(n, 1);
    tr.err_line_color  = [0.5, 0.5, 0.5];
    tr.err_cap_color   = [0.5, 0.5, 0.5];
    tr.err_line_width  = 1.0;
    tr.err_cap_width   = 1.0;
    tr.err_cap_size    = 3.0;
    tr.err_cap_visible = true;
end

% ---------------------------------------------------------------------------
% Surface extraction
% ---------------------------------------------------------------------------
function sf = extract_surface(surf_obj, ax_h)
    sf = struct();
    sf.colormap_name = '';
    sf.colorbar_label = '';
    sf.colorbar_orientation = 'vertical';
    sf.has_colorbar = false;
    sf.uniform_grid = true;
    sf.alpha = 1.0;

    % Check for colorbar
    cb = findobj(ax_h.Parent, 'Type', 'colorbar');
    if ~isempty(cb)
        sf.has_colorbar = true;
        sf.colorbar_label = char(cb(1).Label.String);
        if strcmp(cb(1).Location, 'southoutside') || strcmp(cb(1).Location, 'northoutside')
            sf.colorbar_orientation = 'horizontal';
        end
    end

    % Extract colormap (current figure colormap, 256 entries)
    cmap_data = colormap(ax_h);
    alpha_col  = ones(size(cmap_data, 1), 1);
    sf.cmap = [cmap_data, alpha_col];

    % Grid data
    if isprop(surf_obj, 'XData')
        sf.x_grid = double(surf_obj.XData);
        sf.y_grid = double(surf_obj.YData);
        sf.z_grid = double(surf_obj.ZData);
    else
        sf.x_grid = [];
        sf.y_grid = [];
        sf.z_grid = [];
    end
end

% ---------------------------------------------------------------------------
% Helpers
% ---------------------------------------------------------------------------
function mk = matlab_marker_to_graf(matlab_mk)
    switch matlab_mk
        case 'o',    mk = 'o';
        case '+',    mk = '+';
        case '^',    mk = '^';
        case 'v',    mk = 'v';
        case 's',    mk = '[]';
        case '.',    mk = '.';
        case 'x',    mk = 'x';
        case '*',    mk = '*';
        case '|',    mk = '|';
        case '_',    mk = '_';
        otherwise,   mk = 'None';
    end
end

function [nrows, ncols] = detect_grid(fig, axes_list)
    % Heuristic: count unique normalized y and x positions.
    n = numel(axes_list);
    if n <= 1
        nrows = 1; ncols = 1; return;
    end
    ys = zeros(n, 1); xs = zeros(n, 1);
    for i = 1:n
        axes_list(i).Units = 'normalized';
        pos = axes_list(i).Position;
        xs(i) = round(pos(1) * 10) / 10;
        ys(i) = round(pos(2) * 10) / 10;
    end
    ncols = numel(unique(xs));
    nrows = numel(unique(ys));
end

function [r, c] = idx_to_rc(idx, ncols)
    r = ceil(idx / ncols);
    c = mod(idx - 1, ncols) + 1;
end
