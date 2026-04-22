function graf_save(g, filepath)
% GRAF_SAVE  Write a GrAF struct to a .graf HDF5 file.
%
%   graf_save(g, filepath)
%
%   g must be a struct produced by graf_load or graf_from_fig.
%   Overwrites filepath if it already exists.
%
%   Compatible with MATLAB 2020b.

    % Delete existing file so h5create starts fresh.
    if exist(filepath, 'file')
        delete(filepath);
    end

    % --- Root scalars ---
    hdf5_write_str(filepath, '/supertitle', g.supertitle);
    h5create(filepath, '/fig_width_cm',  1, 'Datatype', 'double');
    h5write( filepath, '/fig_width_cm',  double(g.fig_width_cm));
    h5create(filepath, '/fig_height_cm', 1, 'Datatype', 'double');
    h5write( filepath, '/fig_height_cm', double(g.fig_height_cm));

    % Stub groups required by the format
    hdf5_create_group(filepath, '/style');
    hdf5_create_group(filepath, '/info');
    hdf5_create_group(filepath, '/axes');

    % --- Axes ---
    ax_names = fieldnames(g.axes);
    for ai = 1:numel(ax_names)
        ax_name = ax_names{ai};
        ax_path = ['/axes/' ax_name];
        write_axis(filepath, ax_path, g.axes.(ax_name));
    end
end

% ---------------------------------------------------------------------------
% Axis
% ---------------------------------------------------------------------------
function write_axis(filepath, ax_path, ax)
    hdf5_write_str(filepath, [ax_path '/axis_type'], ax.axis_type);
    hdf5_write_str(filepath, [ax_path '/title'],     ax.title);

    h5create(filepath, [ax_path '/grid_on'],  1, 'Datatype', 'int8');
    h5write( filepath, [ax_path '/grid_on'],  int8(ax.grid_on));

    pos = int64(ax.position(:));
    h5create(filepath, [ax_path '/position'], numel(pos), 'Datatype', 'int64');
    h5write( filepath, [ax_path '/position'], pos);

    spn = int64(ax.span(:));
    h5create(filepath, [ax_path '/span'], numel(spn), 'Datatype', 'int64');
    h5write( filepath, [ax_path '/span'], spn);

    % Relative size (empty array)
    h5create(filepath, [ax_path '/relative_size'], [1 0], 'Datatype', 'double');

    write_scale(filepath, [ax_path '/x_axis'],   ax.x_axis);
    write_scale(filepath, [ax_path '/y_axis_L'], ax.y_axis_L);
    write_scale(filepath, [ax_path '/y_axis_R'], ax.y_axis_R);
    write_scale(filepath, [ax_path '/z_axis'],   ax.z_axis);

    % Traces
    hdf5_create_group(filepath, [ax_path '/traces']);
    if isstruct(ax.traces)
        tr_names = fieldnames(ax.traces);
        for ti = 1:numel(tr_names)
            tr_name = tr_names{ti};
            write_trace(filepath, [ax_path '/traces/' tr_name], ax.traces.(tr_name));
        end
    end

    % Surfaces
    hdf5_create_group(filepath, [ax_path '/surfaces']);
    if isstruct(ax.surfaces)
        sf_names = fieldnames(ax.surfaces);
        for si = 1:numel(sf_names)
            sf_name = sf_names{si};
            write_surface(filepath, [ax_path '/surfaces/' sf_name], ax.surfaces.(sf_name));
        end
    end
end

% ---------------------------------------------------------------------------
% Scale
% ---------------------------------------------------------------------------
function write_scale(filepath, sc_path, sc)
    h5create(filepath, [sc_path '/is_valid'], 1, 'Datatype', 'int8');
    h5write( filepath, [sc_path '/is_valid'], int8(sc.is_valid));

    hdf5_write_str(filepath, [sc_path '/label'], sc.label);

    h5create(filepath, [sc_path '/val_min'], 1, 'Datatype', 'double');
    h5write( filepath, [sc_path '/val_min'], double(sc.val_min));
    h5create(filepath, [sc_path '/val_max'], 1, 'Datatype', 'double');
    h5write( filepath, [sc_path '/val_max'], double(sc.val_max));

    tl = double(sc.tick_list(:));
    if isempty(tl)
        h5create(filepath, [sc_path '/tick_list'], [1 0], 'Datatype', 'double');
    else
        h5create(filepath, [sc_path '/tick_list'], numel(tl), 'Datatype', 'double');
        h5write( filepath, [sc_path '/tick_list'], tl);
    end

    write_str_array(filepath, [sc_path '/tick_label_list'], sc.tick_label_list);

    ml = double(sc.minor_tick_list(:));
    if isempty(ml)
        h5create(filepath, [sc_path '/minor_tick_list'], [1 0], 'Datatype', 'double');
    else
        h5create(filepath, [sc_path '/minor_tick_list'], numel(ml), 'Datatype', 'double');
        h5write( filepath, [sc_path '/minor_tick_list'], ml);
    end
end

% ---------------------------------------------------------------------------
% Trace
% ---------------------------------------------------------------------------
function write_trace(filepath, tr_path, tr)
    hdf5_write_str(filepath, [tr_path '/trace_type'],   tr.trace_type);
    hdf5_write_str(filepath, [tr_path '/display_name'], tr.display_name);
    hdf5_write_str(filepath, [tr_path '/line_type'],    tr.line_type);
    hdf5_write_str(filepath, [tr_path '/marker_type'],  tr.marker_type);

    write_float_vec(filepath, [tr_path '/x_data'], tr.x_data);
    write_float_vec(filepath, [tr_path '/y_data'], tr.y_data);
    write_float_vec(filepath, [tr_path '/z_data'], tr.z_data);

    write_float_vec(filepath, [tr_path '/line_color'],   tr.line_color);
    write_float_vec(filepath, [tr_path '/marker_color'], tr.marker_color);

    write_scalar(filepath, [tr_path '/line_width'],  tr.line_width);
    write_scalar(filepath, [tr_path '/marker_size'], tr.marker_size);
    write_scalar(filepath, [tr_path '/alpha'],       tr.alpha);

    h5create(filepath, [tr_path '/use_yaxis_R'], 1, 'Datatype', 'int8');
    h5write( filepath, [tr_path '/use_yaxis_R'], int8(tr.use_yaxis_R));

    % Error bars
    h5create(filepath, [tr_path '/has_error_bars'], 1, 'Datatype', 'int8');
    h5write( filepath, [tr_path '/has_error_bars'], int8(tr.has_error_bars));

    write_float_vec(filepath, [tr_path '/x_err_neg'], tr.x_err_neg);
    write_float_vec(filepath, [tr_path '/x_err_pos'], tr.x_err_pos);
    write_float_vec(filepath, [tr_path '/y_err_neg'], tr.y_err_neg);
    write_float_vec(filepath, [tr_path '/y_err_pos'], tr.y_err_pos);
    write_float_vec(filepath, [tr_path '/err_line_color'], tr.err_line_color);
    write_float_vec(filepath, [tr_path '/err_cap_color'],  tr.err_cap_color);

    write_scalar(filepath, [tr_path '/err_line_width'], tr.err_line_width);
    write_scalar(filepath, [tr_path '/err_cap_width'],  tr.err_cap_width);
    write_scalar(filepath, [tr_path '/err_cap_size'],   tr.err_cap_size);

    h5create(filepath, [tr_path '/err_cap_visible'], 1, 'Datatype', 'int8');
    h5write( filepath, [tr_path '/err_cap_visible'], int8(tr.err_cap_visible));
end

% ---------------------------------------------------------------------------
% Surface
% ---------------------------------------------------------------------------
function write_surface(filepath, sf_path, sf)
    % cmap: (N,4) in MATLAB → stored as (N,4) in Python (C order).
    % Transpose before writing so Python reads it correctly.
    cmap = double(sf.cmap);   % MATLAB: rows=colors, cols=RGBA
    h5create(filepath, [sf_path '/cmap'], fliplr(size(cmap)), 'Datatype', 'double');
    h5write( filepath, [sf_path '/cmap'], cmap');

    hdf5_write_str(filepath, [sf_path '/colormap_name'],        sf.colormap_name);
    hdf5_write_str(filepath, [sf_path '/colorbar_label'],       sf.colorbar_label);
    hdf5_write_str(filepath, [sf_path '/colorbar_orientation'], sf.colorbar_orientation);

    h5create(filepath, [sf_path '/uniform_grid'], 1, 'Datatype', 'int8');
    h5write( filepath, [sf_path '/uniform_grid'], int8(sf.uniform_grid));
    h5create(filepath, [sf_path '/has_colorbar'],  1, 'Datatype', 'int8');
    h5write( filepath, [sf_path '/has_colorbar'],  int8(sf.has_colorbar));

    write_scalar(filepath, [sf_path '/alpha'], sf.alpha);

    % 2D grids: MATLAB arrays are column-major; write transposed so Python
    % reads them in the expected row-major (C) order.
    write_float_grid(filepath, [sf_path '/x_grid'], sf.x_grid);
    write_float_grid(filepath, [sf_path '/y_grid'], sf.y_grid);
    write_float_grid(filepath, [sf_path '/z_grid'], sf.z_grid);
end

% ---------------------------------------------------------------------------
% Low-level helpers
% ---------------------------------------------------------------------------

function write_scalar(filepath, dset_path, val)
    h5create(filepath, dset_path, 1, 'Datatype', 'double');
    h5write( filepath, dset_path, double(val));
end

function write_float_vec(filepath, dset_path, vec)
    v = double(vec(:));
    if isempty(v)
        h5create(filepath, dset_path, [1 0], 'Datatype', 'double');
    else
        h5create(filepath, dset_path, numel(v), 'Datatype', 'double');
        h5write( filepath, dset_path, v);
    end
end

function write_float_grid(filepath, dset_path, mat)
    % mat is a 2D MATLAB matrix (row-major semantics when transposed for HDF5).
    m = double(mat);
    sz = fliplr(size(m));   % HDF5 dimension order is reversed vs MATLAB
    h5create(filepath, dset_path, sz, 'Datatype', 'double');
    h5write( filepath, dset_path, m');
end

function write_str_array(filepath, dset_path, c)
% Write a cell array of strings as a variable-length UTF-8 string dataset.
    if isempty(c)
        % Write as empty dataset; simplest approach: write a placeholder.
        hdf5_write_str_vec(filepath, dset_path, {});
        return;
    end
    hdf5_write_str_vec(filepath, dset_path, c);
end

function hdf5_write_str(filepath, dset_path, str)
% Write a scalar variable-length UTF-8 string using the low-level HDF5 API.
    if ~ischar(str)
        str = char(str);
    end

    fid  = H5F.open(filepath, 'H5F_ACC_RDWR', 'H5P_DEFAULT');
    cleanup_f = onCleanup(@() H5F.close(fid));

    % Build variable-length string type
    tid = H5T.copy('H5T_C_S1');
    H5T.set_size(tid, 'H5T_VARIABLE');
    H5T.set_strpad(tid, 'H5T_STR_NULLTERM');
    H5T.set_cset(tid, 'H5T_CSET_UTF8');

    sid = H5S.create('H5S_SCALAR');

    % Create intermediate groups if needed
    ensure_groups(fid, dset_path);

    did = H5D.create(fid, dset_path, tid, sid, 'H5P_DEFAULT');
    H5D.write(did, tid, 'H5S_ALL', 'H5S_ALL', 'H5P_DEFAULT', {str});

    H5D.close(did);
    H5S.close(sid);
    H5T.close(tid);
end

function hdf5_write_str_vec(filepath, dset_path, c)
% Write a 1-D cell array of strings as variable-length UTF-8 strings.
    if ~iscell(c)
        c = {c};
    end
    n = numel(c);

    fid  = H5F.open(filepath, 'H5F_ACC_RDWR', 'H5P_DEFAULT');
    cleanup_f = onCleanup(@() H5F.close(fid));

    tid = H5T.copy('H5T_C_S1');
    H5T.set_size(tid, 'H5T_VARIABLE');
    H5T.set_strpad(tid, 'H5T_STR_NULLTERM');
    H5T.set_cset(tid, 'H5T_CSET_UTF8');

    if n == 0
        sid = H5S.create_simple(1, 0, []);
    else
        sid = H5S.create_simple(1, n, []);
    end

    ensure_groups(fid, dset_path);

    did = H5D.create(fid, dset_path, tid, sid, 'H5P_DEFAULT');
    if n > 0
        H5D.write(did, tid, 'H5S_ALL', 'H5S_ALL', 'H5P_DEFAULT', c);
    end

    H5D.close(did);
    H5S.close(sid);
    H5T.close(tid);
end

function hdf5_create_group(filepath, grp_path)
% Touch a group so descendant datasets can be created.
    fid = H5F.open(filepath, 'H5F_ACC_RDWR', 'H5P_DEFAULT');
    cleanup_f = onCleanup(@() H5F.close(fid));
    ensure_group_fid(fid, grp_path);
end

function ensure_groups(fid, dset_path)
% Create all parent groups of dset_path that don't already exist.
    parts = strsplit(dset_path, '/');
    % parts{1} is '' (leading slash), last is the dataset name
    for k = 2:numel(parts)-1
        grp = strjoin(parts(1:k), '/');
        try
            gid = H5G.open(fid, grp);
            H5G.close(gid);
        catch
            gid = H5G.create(fid, grp, 0);
            H5G.close(gid);
        end
    end
end

function ensure_group_fid(fid, grp_path)
    parts = strsplit(grp_path, '/');
    for k = 2:numel(parts)
        grp = strjoin(parts(1:k), '/');
        try
            gid = H5G.open(fid, grp);
            H5G.close(gid);
        catch
            gid = H5G.create(fid, grp, 0);
            H5G.close(gid);
        end
    end
end
