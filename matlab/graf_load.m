function g = graf_load(filepath)
% GRAF_LOAD  Read a .graf HDF5 file into a MATLAB struct.
%
%   g = graf_load(filepath)
%
%   Returns a struct g with fields mirroring the GrAF format:
%     g.supertitle      - string
%     g.fig_width_cm    - scalar double (figure width in cm)
%     g.fig_height_cm   - scalar double (figure height in cm)
%     g.axes            - struct array indexed by axis name (Ax0, Ax1, ...)
%       .axis_type      - string
%       .title          - string
%       .grid_on        - logical
%       .position       - [row, col] int
%       .span           - [rowspan, colspan] int
%       .x_axis         - scale struct (label, val_min, val_max, tick_list, ...)
%       .y_axis_L       - scale struct
%       .y_axis_R       - scale struct
%       .z_axis         - scale struct
%       .traces         - struct indexed by trace name (Tr0, Tr1, ...)
%       .surfaces       - struct indexed by surface name (Sf0, Sf1, ...)

    info = h5info(filepath);
    g = struct();

    % --- Root-level scalars / strings ---
    g.supertitle    = hdf5_read_str(filepath, '/supertitle');
    % fig_width_cm / fig_height_cm were added in a later format revision;
    % fall back to the matplotlib default size for older files.
    g.fig_width_cm  = hdf5_read_scalar(filepath, '/fig_width_cm',  6.4 * 2.54);
    g.fig_height_cm = hdf5_read_scalar(filepath, '/fig_height_cm', 4.8 * 2.54);

    % --- Axes ---
    g.axes = struct();
    ax_group = hdf5_find_group(info, 'axes');
    if ~isempty(ax_group)
        for ai = 1:numel(ax_group.Groups)
            ax_info = ax_group.Groups(ai);
            ax_name = last_token(ax_info.Name);
            ax_path = ['/axes/' ax_name];
            ax_s = read_axis(filepath, ax_path, ax_info);
            g.axes.(ax_name) = ax_s;
        end
    end
end

% ---------------------------------------------------------------------------
% Axis
% ---------------------------------------------------------------------------
function ax = read_axis(filepath, ax_path, ax_info)
    ax = struct();
    ax.axis_type = hdf5_read_str(filepath, [ax_path '/axis_type']);
    ax.title     = hdf5_read_str(filepath, [ax_path '/title']);
    ax.grid_on   = hdf5_read_bool(filepath, [ax_path '/grid_on']);
    ax.position  = double(h5read(filepath, [ax_path '/position']));
    ax.span      = double(h5read(filepath, [ax_path '/span']));

    ax.x_axis   = read_scale(filepath, [ax_path '/x_axis']);
    ax.y_axis_L = read_scale(filepath, [ax_path '/y_axis_L']);
    ax.y_axis_R = read_scale(filepath, [ax_path '/y_axis_R']);
    ax.z_axis   = read_scale(filepath, [ax_path '/z_axis']);

    % Traces
    ax.traces = struct();
    tr_group = hdf5_find_group(ax_info, 'traces');
    if ~isempty(tr_group)
        for ti = 1:numel(tr_group.Groups)
            tr_info = tr_group.Groups(ti);
            tr_name = last_token(tr_info.Name);
            tr_path = [ax_path '/traces/' tr_name];
            ax.traces.(tr_name) = read_trace(filepath, tr_path);
        end
    end

    % Surfaces
    ax.surfaces = struct();
    sf_group = hdf5_find_group(ax_info, 'surfaces');
    if ~isempty(sf_group)
        for si = 1:numel(sf_group.Groups)
            sf_info = sf_group.Groups(si);
            sf_name = last_token(sf_info.Name);
            sf_path = [ax_path '/surfaces/' sf_name];
            ax.surfaces.(sf_name) = read_surface(filepath, sf_path);
        end
    end
end

% ---------------------------------------------------------------------------
% Scale (axis metadata)
% ---------------------------------------------------------------------------
function sc = read_scale(filepath, sc_path)
    sc = struct();
    sc.is_valid  = hdf5_read_bool(filepath, [sc_path '/is_valid']);
    sc.label     = hdf5_read_str(filepath, [sc_path '/label']);
    sc.val_min   = double(h5read(filepath, [sc_path '/val_min']));
    sc.val_max   = double(h5read(filepath, [sc_path '/val_max']));
    tick_raw = h5read(filepath, [sc_path '/tick_list']);
    sc.tick_list = double(tick_raw(:))';
    sc.tick_label_list = hdf5_read_str_array(filepath, [sc_path '/tick_label_list']);
    minor_raw = h5read(filepath, [sc_path '/minor_tick_list']);
    sc.minor_tick_list = double(minor_raw(:))';
end

% ---------------------------------------------------------------------------
% Trace
% ---------------------------------------------------------------------------
function tr = read_trace(filepath, tr_path)
    tr = struct();
    tr.trace_type    = hdf5_read_str(filepath, [tr_path '/trace_type']);
    tr.display_name  = hdf5_read_str(filepath, [tr_path '/display_name']);
    tr.line_type     = hdf5_read_str(filepath, [tr_path '/line_type']);
    tr.marker_type   = hdf5_read_str(filepath, [tr_path '/marker_type']);

    tr.x_data = double(h5read(filepath, [tr_path '/x_data']));
    tr.y_data = double(h5read(filepath, [tr_path '/y_data']));
    tr.z_data = double(h5read(filepath, [tr_path '/z_data']));

    tr.line_color   = double(h5read(filepath, [tr_path '/line_color']));
    tr.marker_color = double(h5read(filepath, [tr_path '/marker_color']));
    tr.line_width   = double(h5read(filepath, [tr_path '/line_width']));
    tr.marker_size  = double(h5read(filepath, [tr_path '/marker_size']));
    tr.alpha        = double(h5read(filepath, [tr_path '/alpha']));
    tr.use_yaxis_R  = hdf5_read_bool(filepath, [tr_path '/use_yaxis_R']);

    % Error bar fields
    tr.has_error_bars  = hdf5_read_bool(filepath, [tr_path '/has_error_bars']);
    tr.x_err_neg       = double(h5read(filepath, [tr_path '/x_err_neg']));
    tr.x_err_pos       = double(h5read(filepath, [tr_path '/x_err_pos']));
    tr.y_err_neg       = double(h5read(filepath, [tr_path '/y_err_neg']));
    tr.y_err_pos       = double(h5read(filepath, [tr_path '/y_err_pos']));
    tr.err_line_color  = double(h5read(filepath, [tr_path '/err_line_color']));
    tr.err_cap_color   = double(h5read(filepath, [tr_path '/err_cap_color']));
    tr.err_line_width  = double(h5read(filepath, [tr_path '/err_line_width']));
    tr.err_cap_width   = double(h5read(filepath, [tr_path '/err_cap_width']));
    tr.err_cap_size    = double(h5read(filepath, [tr_path '/err_cap_size']));
    tr.err_cap_visible = hdf5_read_bool(filepath, [tr_path '/err_cap_visible']);
end

% ---------------------------------------------------------------------------
% Surface
% ---------------------------------------------------------------------------
function sf = read_surface(filepath, sf_path)
    sf = struct();
    sf.cmap          = double(h5read(filepath, [sf_path '/cmap']))';   % transpose: Python C-order → MATLAB column-major
    sf.colormap_name = hdf5_read_str(filepath, [sf_path '/colormap_name']);
    sf.uniform_grid  = hdf5_read_bool(filepath, [sf_path '/uniform_grid']);
    sf.has_colorbar  = hdf5_read_bool(filepath, [sf_path '/has_colorbar']);
    sf.colorbar_label       = hdf5_read_str(filepath, [sf_path '/colorbar_label']);
    sf.colorbar_orientation = hdf5_read_str(filepath, [sf_path '/colorbar_orientation']);
    sf.alpha = double(h5read(filepath, [sf_path '/alpha']));

    % 2D grids: Python stores row-major (C order); h5read gives column-major,
    % which already corresponds to the correct layout for MATLAB surf/pcolor.
    sf.x_grid = double(h5read(filepath, [sf_path '/x_grid']))';
    sf.y_grid = double(h5read(filepath, [sf_path '/y_grid']))';
    sf.z_grid = double(h5read(filepath, [sf_path '/z_grid']))';
end

% ---------------------------------------------------------------------------
% HDF5 helpers
% ---------------------------------------------------------------------------

function val = hdf5_read_scalar(filepath, dset_path, default_val)
% Read a scalar double dataset; return default_val if the dataset is absent.
    try
        val = double(h5read(filepath, dset_path));
    catch
        val = default_val;
    end
end

function b = hdf5_read_bool(filepath, dset_path)
% Read a scalar HDF5 boolean and return a proper MATLAB logical scalar.
% h5read may return uint8, logical, or a 1x1 array — handle all cases.
    try
        raw = h5read(filepath, dset_path);
        b = logical(raw(1) ~= 0);
    catch
        b = false;
    end
end

function s = hdf5_read_str(filepath, dset_path)
% Read a scalar HDF5 string dataset.
% Handles variable-length UTF-8, fixed-length char, cell wrapping, and
% null terminators that MATLAB may leave in the result.
    try
        raw = h5read(filepath, dset_path);
        s = normalize_str(raw);
    catch
        s = '';
    end
end

function arr = hdf5_read_str_array(filepath, dset_path)
% Read a 1-D array of HDF5 strings; returns a cell array of clean strings.
    try
        raw = h5read(filepath, dset_path);
        if ischar(raw)
            arr = {normalize_str(raw)};
        elseif iscell(raw)
            arr = cellfun(@normalize_str, raw, 'UniformOutput', false);
        else
            arr = {};
        end
    catch
        arr = {};
    end
end

function s = normalize_str(raw)
% Convert any HDF5 string value to a clean MATLAB char row vector.
% Unwraps cells, converts uint8 UTF-8 bytes, strips null chars and whitespace.
    if iscell(raw)
        raw = raw{1};
    end
    if isa(raw, 'uint8') || isa(raw, 'int8')
        s = native2unicode(raw(:)', 'UTF-8');
    elseif ischar(raw)
        s = raw;
    else
        s = char(raw);
    end
    % Strip embedded null terminators then trim surrounding whitespace
    s = strtrim(strrep(s, char(0), ''));
end

function grp = hdf5_find_group(parent_info, name)
% Return the sub-group info struct whose name ends in /name, or [].
    grp = [];
    for i = 1:numel(parent_info.Groups)
        if strcmp(last_token(parent_info.Groups(i).Name), name)
            grp = parent_info.Groups(i);
            return;
        end
    end
end

function tok = last_token(hdf5_path)
% Return the last '/'-delimited token of an HDF5 path.
    parts = strsplit(hdf5_path, '/');
    tok = parts{end};
end
