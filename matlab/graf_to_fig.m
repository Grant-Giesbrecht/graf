function fig = graf_to_fig(g, varargin)
% GRAF_TO_FIG  Reconstruct a MATLAB figure from a GrAF struct.
%
%   fig = graf_to_fig(g)
%   fig = graf_to_fig(g, 'Scale', 1.5)
%   fig = graf_to_fig(g, 'Title', 'My Window')
%
%   Options (name-value pairs):
%     'Scale'  - multiplicative size scale factor (default 1.0)
%     'Title'  - figure window title string
%
%   Returns the MATLAB figure handle.

    p = inputParser();
    p.addParameter('Scale', 1.0);
    p.addParameter('Title', '');
    p.parse(varargin{:});
    scale = p.Results.Scale;
    win_title = p.Results.Title;

    % Figure size (cm → inches for MATLAB)
    cm_per_inch = 2.54;
    w_in = g.fig_width_cm  / cm_per_inch * scale;
    h_in = g.fig_height_cm / cm_per_inch * scale;

    if isempty(win_title)
        fig = figure('Units', 'inches', 'Position', [1 1 w_in h_in]);
    else
        fig = figure('Name', win_title, 'Units', 'inches', 'Position', [1 1 w_in h_in]);
    end

    if ~isempty(g.supertitle)
        sgtitle(g.supertitle);
    end

    % Collect axes, determine grid layout
    ax_names = fieldnames(g.axes);
    n_axes = numel(ax_names);
    if n_axes == 0
        return;
    end

    % Determine subplot grid size from position/span fields.
    % position is 0-based [row, col]; convert to 1-based for MATLAB.
    max_row = 1; max_col = 1;
    for ai = 1:n_axes
        ax_s = g.axes.(ax_names{ai});
        r = (ax_s.position(1) + 1) + ax_s.span(1) - 1;
        c = (ax_s.position(2) + 1) + ax_s.span(2) - 1;
        max_row = max(max_row, r);
        max_col = max(max_col, c);
    end

    mpl_handles = struct();   % ax_name → matlab axes handle

    for ai = 1:n_axes
        ax_name = ax_names{ai};
        ax_s    = g.axes.(ax_name);

        % Convert 0-based position to 1-based row/col
        row   = ax_s.position(1) + 1;
        col   = ax_s.position(2) + 1;
        rspan = ax_s.span(1);
        cspan = ax_s.span(2);

        % Convert row/col + span to linear subplot indices
        idx_start = (row - 1) * max_col + col;
        if rspan == 1 && cspan == 1
            ax_h = subplot(max_row, max_col, idx_start);
        else
            idx_end = (row + rspan - 2) * max_col + (col + cspan - 1);
            ax_h = subplot(max_row, max_col, idx_start:idx_end);
        end
        mpl_handles.(ax_name) = ax_h;

        hold(ax_h, 'on');

        ax_type = ax_s.axis_type;

        if strcmp(ax_type, 'AXIS_LINE2D')
            render_line2d(ax_h, ax_s);
        elseif strcmp(ax_type, 'AXIS_LINE3D')
            render_line3d(ax_h, ax_s);
        elseif strcmp(ax_type, 'AXIS_SURFACE') || strcmp(ax_type, 'AXIS_IMAGE')
            render_surface(ax_h, ax_s);
        end

        % Common axis formatting
        apply_axis_labels(ax_h, ax_s);
        if ax_s.grid_on
            axes(ax_h);
            grid on;
        end
    end
end

% ---------------------------------------------------------------------------
% 2-D / 3-D line axes  (axis_type is always AXIS_LINE2D; detect 3D via trace_type)
% ---------------------------------------------------------------------------
function render_line2d(ax_h, ax_s)
    tr_names = fieldnames(ax_s.traces);

    % Pre-scan: does any trace use the right y-axis?
    has_right = false;
    for ti = 1:numel(tr_names)
        if ax_s.traces.(tr_names{ti}).use_yaxis_R
            has_right = true;
            break;
        end
    end

    is_3d = false;
    for ti = 1:numel(tr_names)
        tr = ax_s.traces.(tr_names{ti});
        if tr.has_error_bars
            if has_right; yyaxis(ax_h, 'left'); end
            draw_errorbar(ax_h, tr);
        elseif strcmp(tr.trace_type, 'TRACE_LINE3D')
            draw_line3d(ax_h, tr);
            is_3d = true;
        else
            if has_right
                if tr.use_yaxis_R
                    yyaxis(ax_h, 'right');
                else
                    yyaxis(ax_h, 'left');
                end
            end
            draw_line2d(ax_h, tr);
        end
    end

    % Apply right y-axis label and limits, then leave left axis active
    % so that apply_axis_labels (called by the caller) targets the left side.
    if has_right
        yyaxis(ax_h, 'right');
        if ~isempty(ax_s.y_axis_R.label)
            ylabel(ax_h, ax_s.y_axis_R.label);
        end
        if ax_s.y_axis_R.is_valid
            ylim(ax_h, [ax_s.y_axis_R.val_min, ax_s.y_axis_R.val_max]);
        end
        yyaxis(ax_h, 'left');
    end

    if is_3d
        if ax_s.z_axis.is_valid && ~isempty(ax_s.z_axis.label)
            zlabel(ax_h, ax_s.z_axis.label);
        end
        if ax_s.z_axis.is_valid
            zlim(ax_h, [ax_s.z_axis.val_min, ax_s.z_axis.val_max]);
        end
        view(ax_h, 3);
    end
end

function draw_line2d(ax_h, tr)
    % yyaxis switching is handled by render_line2d before this call.
    x = tr.x_data(:);
    y = tr.y_data(:);
    ls    = graf_linestyle(tr.line_type);
    mk    = graf_marker(tr.marker_type);
    col   = double(tr.line_color(:)');
    mkcol = double(tr.marker_color(:)');

    h = plot(ax_h, x, y, ...
        'LineStyle',       ls, ...
        'Marker',          mk, ...
        'LineWidth',       tr.line_width, ...
        'MarkerSize',      tr.marker_size, ...
        'Color',           col, ...
        'MarkerFaceColor', mkcol, ...
        'DisplayName',     tr.display_name);

    if tr.alpha < 1.0
        h.Color(4) = tr.alpha;
    end
end

function draw_line3d(ax_h, tr)
    x   = tr.x_data(:);
    y   = tr.y_data(:);
    z   = tr.z_data(:);
    col = double(tr.line_color(:)');
    plot3(ax_h, x, y, z, ...
        'LineStyle',   graf_linestyle(tr.line_type), ...
        'Marker',      graf_marker(tr.marker_type), ...
        'LineWidth',   tr.line_width, ...
        'MarkerSize',  tr.marker_size, ...
        'Color',       col, ...
        'DisplayName', tr.display_name);
end

function draw_errorbar(ax_h, tr)
    x = tr.x_data(:);
    y = tr.y_data(:);

    y_err_neg = tr.y_err_neg(:);
    y_err_pos = tr.y_err_pos(:);
    x_err_neg = tr.x_err_neg(:);
    x_err_pos = tr.x_err_pos(:);

    has_yerr = any(y_err_neg > 0) || any(y_err_pos > 0);
    has_xerr = any(x_err_neg > 0) || any(x_err_pos > 0);

    yerr = [];
    if has_yerr
        yerr = [y_err_neg'; y_err_pos'];
    end
    xerr = [];
    if has_xerr
        xerr = [x_err_neg'; x_err_pos'];
    end

    ls  = graf_linestyle(tr.line_type);
    mk  = graf_marker(tr.marker_type);
    col = double(tr.line_color(:)');
    ecol = double(tr.err_line_color(:)');
    ccol = double(tr.err_cap_color(:)');

    args = {'LineStyle', ls, 'Marker', mk, ...
            'LineWidth', tr.line_width, 'MarkerSize', tr.marker_size, ...
            'Color', col, ...
            'MarkerFaceColor', double(tr.marker_color(:)'), ...
            'DisplayName', tr.display_name, ...
            'CapSize', tr.err_cap_size * 2, ...   % factor-of-2 as in Python
            'LineWidth', tr.err_line_width};

    if ~isempty(yerr) && ~isempty(xerr)
        errorbar(ax_h, x, y, yerr(1,:)', yerr(2,:)', xerr(1,:)', xerr(2,:)', args{:});
    elseif ~isempty(yerr)
        errorbar(ax_h, x, y, yerr(1,:)', yerr(2,:)', args{:});
    elseif ~isempty(xerr)
        errorbar(ax_h, x, y, [], [], xerr(1,:)', xerr(2,:)', args{:});
    else
        errorbar(ax_h, x, y, zeros(size(y)), zeros(size(y)), args{:});
    end
end

% ---------------------------------------------------------------------------
% 3-D line axes
% ---------------------------------------------------------------------------
function render_line3d(ax_h, ax_s)
    % plot3 on an existing axes handle automatically enables 3-D rendering.
    tr_names = fieldnames(ax_s.traces);
    for ti = 1:numel(tr_names)
        tr = ax_s.traces.(tr_names{ti});
        x = tr.x_data(:);
        y = tr.y_data(:);
        z = tr.z_data(:);
        col = double(tr.line_color(:)');
        plot3(ax_h, x, y, z, ...
            'LineStyle', graf_linestyle(tr.line_type), ...
            'Marker',    graf_marker(tr.marker_type), ...
            'LineWidth', tr.line_width, ...
            'Color',     col, ...
            'DisplayName', tr.display_name);
    end

    % Z-axis label and limits
    if ax_s.z_axis.is_valid && ~isempty(ax_s.z_axis.label)
        zlabel(ax_h, ax_s.z_axis.label);
    end
    if ax_s.z_axis.is_valid
        zlim(ax_h, [ax_s.z_axis.val_min, ax_s.z_axis.val_max]);
    end

    view(ax_h, 3);
end

% ---------------------------------------------------------------------------
% Surface / image axes
% ---------------------------------------------------------------------------
function render_surface(ax_h, ax_s)
    sf_names = fieldnames(ax_s.surfaces);
    if isempty(sf_names)
        return;
    end
    sf = ax_s.surfaces.(sf_names{1});
    Z = double(sf.z_grid);
    X = double(sf.x_grid);
    Y = double(sf.y_grid);

    [nrx, ncx] = size(X);
    [nrz, ncz] = size(Z);

    if nrx == nrz + 1 && ncx == ncz + 1
        % Corner-based grid (pcolormesh style): X/Y are (M+1)x(N+1), Z is MxN.
        % MATLAB's pcolor needs all three the same size; pad Z with a repeated
        % border row and column (the extra cells are not rendered with flat shading).
        Z_plot = Z([1:end, end], [1:end, end]);
        pcolor(ax_h, X, Y, Z_plot);
        shading(ax_h, 'flat');
    else
        % Centre-based grid (imshow / contourf style)
        pcolor(ax_h, X, Y, Z);
        shading(ax_h, 'interp');
    end

    % Colormap is stored as Nx4 RGBA; MATLAB colormap needs Nx3 RGB.
    if ~isempty(sf.cmap) && size(sf.cmap, 2) >= 3
        colormap(ax_h, sf.cmap(:, 1:3));
    end

    if sf.has_colorbar
        cb = colorbar(ax_h);
        if ~isempty(sf.colorbar_label)
            cb.Label.String = sf.colorbar_label;
        end
        if strcmpi(sf.colorbar_orientation, 'horizontal')
            cb.Location = 'southoutside';
        end
    end
end

% ---------------------------------------------------------------------------
% Common axis formatting
% ---------------------------------------------------------------------------
function apply_axis_labels(ax_h, ax_s)
    if ~isempty(ax_s.title)
        title(ax_h, ax_s.title);
    end
    if ~isempty(ax_s.x_axis.label)
        xlabel(ax_h, ax_s.x_axis.label);
    end
    if ax_s.x_axis.is_valid
        xlim(ax_h, [ax_s.x_axis.val_min, ax_s.x_axis.val_max]);
    end
    if ~isempty(ax_s.y_axis_L.label)
        ylabel(ax_h, ax_s.y_axis_L.label);
    end
    if ax_s.y_axis_L.is_valid
        ylim(ax_h, [ax_s.y_axis_L.val_min, ax_s.y_axis_L.val_max]);
    end
end

% ---------------------------------------------------------------------------
% Style mapping helpers
% ---------------------------------------------------------------------------
function ls = graf_linestyle(graf_ls)
    switch graf_ls
        case '-',    ls = '-';
        case '--',   ls = '--';
        case '-.',   ls = '-.';
        case ':',    ls = ':';
        otherwise,   ls = 'none';
    end
end

function mk = graf_marker(graf_mk)
    switch graf_mk
        case 'o',    mk = 'o';
        case '+',    mk = '+';
        case '^',    mk = '^';
        case 'v',    mk = 'v';
        case '[]',   mk = 's';
        case '.',    mk = '.';
        case 'x',    mk = 'x';
        case '*',    mk = '*';
        case '|',    mk = '|';
        case '_',    mk = '_';
        otherwise,   mk = 'none';
    end
end
