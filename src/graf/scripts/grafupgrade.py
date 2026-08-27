#!/usr/bin/env python
"""graf-upgrade -- rewrite .graf files in the current format version.

GrAF reads older files without this tool: fields added since a file was written
simply take their defaults. Upgrading is worth doing anyway, for two reasons.

  * It makes the defaults explicit. A pre-1.0 file has no font stack and no
    legend state; after upgrading it has both, recorded rather than assumed.
  * It is what lets old format support eventually be dropped. Read-time
    tolerance cannot be removed while unupgraded files are still in use; once
    they have been converted, a future major version can stop carrying it.

The original is never modified in place without a backup, and never silently.
"""

import argparse
import os
import shutil
import sys
import warnings

from graf.base import (
	GRAF_FORMAT_VERSION,
	GRAF_EXTENSION,
	Graf,
	GrafError,
	is_legacy_version,
)


def find_files(paths, recursive=False):
	""" Expand the given paths into a list of .graf files. """

	found = []
	for path in paths:
		if os.path.isdir(path):
			if recursive:
				for root, _dirs, names in os.walk(path):
					found += [os.path.join(root, n) for n in sorted(names)
							  if n.lower().endswith(GRAF_EXTENSION)]
			else:
				found += [os.path.join(path, n) for n in sorted(os.listdir(path))
						  if n.lower().endswith(GRAF_EXTENSION)]
		else:
			found.append(path)
	return found


def file_version(path):
	""" The format version a file declares, or None if it cannot be read. """

	try:
		from stardust.tome import tome_to_dict
		info = tome_to_dict(path).get('info')
		return info.get('version') if isinstance(info, dict) else None
	except Exception:
		return None


def upgrade_file(path, *, backup=True, dry_run=False, verbose=False):
	"""Rewrite one file in the current format.

	Returns one of 'upgraded', 'current', 'would-upgrade', 'failed'.
	"""

	version = file_version(path)

	if version == GRAF_FORMAT_VERSION:
		if verbose:
			print(f"  {path}: already format {GRAF_FORMAT_VERSION}")
		return 'current'

	if version is not None and not is_legacy_version(version):
		print(f"  {path}: format {version} is not upgradable by this version "
			  f"of GrAF (it reads {GRAF_FORMAT_VERSION}).", file=sys.stderr)
		return 'failed'

	if dry_run:
		print(f"  {path}: format {version} -> {GRAF_FORMAT_VERSION}")
		return 'would-upgrade'

	# Read fully before touching anything on disk.
	graf = Graf()
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			graf.read_graf(path)
	except GrafError as e:
		print(f"  {path}: could not be read ({e})", file=sys.stderr)
		return 'failed'
	except Exception as e:
		print(f"  {path}: unexpected error reading ({e})", file=sys.stderr)
		return 'failed'

	if backup:
		backup_path = path + ".bak"
		if os.path.exists(backup_path):
			print(f"  {path}: backup '{backup_path}' already exists; skipping. "
				  f"Move it aside or pass --no-backup.", file=sys.stderr)
			return 'failed'
		shutil.copy2(path, backup_path)

	# Write to a temporary file first, so an interrupted or failing write cannot
	# leave a truncated archive where the original used to be.
	temp_path = path + ".upgrading"
	try:
		graf.write_graf(temp_path, action=f"upgraded from format {version} to {GRAF_FORMAT_VERSION}",
						source_app=f"graf-upgrade {GRAF_FORMAT_VERSION}")
		os.replace(temp_path, path)
	except Exception as e:
		if os.path.exists(temp_path):
			os.remove(temp_path)
		print(f"  {path}: upgrade failed, original untouched ({e})", file=sys.stderr)
		return 'failed'

	print(f"  {path}: {version} -> {GRAF_FORMAT_VERSION}"
		  + (f" (backup: {os.path.basename(path)}.bak)" if backup else ""))
	return 'upgraded'


def build_parser():
	parser = argparse.ArgumentParser(
		prog="graf-upgrade",
		description=f"Rewrite .graf files in format {GRAF_FORMAT_VERSION}.",
		epilog="GrAF reads older files without upgrading them; this makes the "
			   "conversion permanent so support for the old layout can "
			   "eventually be retired.")
	parser.add_argument('paths', nargs='+',
						help="GrAF files, or directories containing them")
	parser.add_argument('-r', '--recursive', action='store_true',
						help="recurse into subdirectories")
	parser.add_argument('-n', '--dry-run', action='store_true',
						help="report what would change, write nothing")
	parser.add_argument('--no-backup', action='store_true',
						help="do not write a .bak copy beside each file")
	parser.add_argument('-v', '--verbose', action='store_true',
						help="also list files already in the current format")
	return parser


def main(argv=None):
	args = build_parser().parse_args(argv)

	files = find_files(args.paths, recursive=args.recursive)
	if not files:
		print("No .graf files found.", file=sys.stderr)
		return 1

	missing = [f for f in files if not os.path.isfile(f)]
	for path in missing:
		print(f"  {path}: not found", file=sys.stderr)
	files = [f for f in files if os.path.isfile(f)]

	if args.dry_run:
		print(f"Dry run — nothing will be written. Target format: {GRAF_FORMAT_VERSION}")

	counts = {'upgraded': 0, 'current': 0, 'would-upgrade': 0, 'failed': len(missing)}
	for path in files:
		counts[upgrade_file(path, backup=not args.no_backup,
							dry_run=args.dry_run, verbose=args.verbose)] += 1

	print()
	if args.dry_run:
		print(f"{counts['would-upgrade']} file(s) would be upgraded, "
			  f"{counts['current']} already current, {counts['failed']} failed.")
	else:
		print(f"{counts['upgraded']} file(s) upgraded, "
			  f"{counts['current']} already current, {counts['failed']} failed.")

	return 1 if counts['failed'] else 0


if __name__ == "__main__":
	sys.exit(main())
