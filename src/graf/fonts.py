"""Font specification and resolution for GrAF.

GrAF separates three things that are easy to conflate, and the separation is the
whole design:

  1. GENERIC ROLES -- 'serif', 'sans-serif', 'monospace'. A closed set of
     *roles*, never family names. No family may claim one as an alias.

  2. THE REQUEST -- an ordered font stack, most specific first, ending in a
     generic role:

         ["MFB Oldstyle", "Georgia", "serif"]

     This is CSS's model, and it is right because it records both the exact face
     the author used AND the class of thing it is. A reader that lacks the exact
     font still knows the intent. Asking for "a specific font" and asking for
     "just a serif" are not two modes; ["serif"] is simply the degenerate stack.

  3. LOCAL RESOLUTION -- what this machine actually has. A user config maps roles
     to concrete families and adds search paths.

Resolution walks the stack, and for each candidate looks in: fonts GrAF bundles,
then user-configured paths, then fonts installed on the system. First hit wins.
If nothing matches, the stack's trailing generic role decides, so a serif request
degrades to another serif rather than jumping font classes.

Files also record `resolved_family`: the family actually in use when the figure
was saved. That is typographic provenance -- without it a reader cannot tell
faithful reproduction from silent substitution.
"""

import json
import os
import platform
import warnings

import matplotlib.font_manager as fm

# ==============================================================================
# Roles and licences
# ==============================================================================

# Generic font roles. A closed set: these are roles, not families, and a family
# must never claim one as an alias -- that conflation is what makes "I want any
# serif" inexpressible.
SERIF = "serif"
SANS_SERIF = "sans-serif"
MONOSPACE = "monospace"

GENERIC_ROLES = (SERIF, SANS_SERIF, MONOSPACE)

# Spellings tolerated on read and normalised to a canonical role. 'sanserif' is
# what pre-1.0 GrAF wrote; it is not a standard spelling and is accepted only so
# early files keep working.
ROLE_ALIASES = {
	"sanserif": SANS_SERIF,
	"sans serif": SANS_SERIF,
	"sans": SANS_SERIF,
	"mono": MONOSPACE,
	"monospaced": MONOSPACE,
	"fixed": MONOSPACE,
}

# Font licences GrAF is willing to redistribute. Each clearly permits bundling
# the font inside a larger package. Anything merely "free to download" or "free
# for personal use" does not qualify -- see assets/fonts/LICENSES/README.md.
ALLOWED_FONT_LICENSES = ("OFL-1.1", "CC0-1.0", "Apache-2.0", "MIT")

# Role used when a stack names no generic role and nothing else resolves.
LAST_RESORT_ROLE = SANS_SERIF

# ==============================================================================
# Weight and style
# ==============================================================================

WEIGHT_NAMES = {
	"thin": 100, "extralight": 200, "ultralight": 200, "light": 300,
	"normal": 400, "regular": 400, "book": 400,
	"medium": 500, "semibold": 600, "demibold": 600,
	"bold": 700, "extrabold": 800, "ultrabold": 800,
	"black": 900, "heavy": 900,
}

NORMAL_WEIGHT = 400
BOLD_WEIGHT = 700

STYLE_NORMAL = "normal"
STYLE_ITALIC = "italic"
STYLE_OBLIQUE = "oblique"
VALID_STYLES = (STYLE_NORMAL, STYLE_ITALIC, STYLE_OBLIQUE)


def normalize_weight(weight):
	"""Coerce a weight to an int in [100, 900].

	Accepts CSS-style numbers and the usual names ('bold', 'light', ...).
	Unrecognised values fall back to normal with a warning rather than raising:
	a weird weight in an old file should not make the figure unopenable.
	"""

	if isinstance(weight, bool):			# bool is an int subclass -- catch first
		return BOLD_WEIGHT if weight else NORMAL_WEIGHT

	if isinstance(weight, (int, float)):
		value = int(weight)
		if 100 <= value <= 900:
			return value
		warnings.warn(f"Font weight {weight} is outside 100-900; using {NORMAL_WEIGHT}.")
		return NORMAL_WEIGHT

	if isinstance(weight, str):
		key = weight.strip().lower().replace('-', '').replace('_', '').replace(' ', '')
		if key in WEIGHT_NAMES:
			return WEIGHT_NAMES[key]
		if key.isdigit():
			return normalize_weight(int(key))

	warnings.warn(f"Unrecognised font weight {weight!r}; using {NORMAL_WEIGHT}.")
	return NORMAL_WEIGHT


def normalize_style(style):
	""" Coerce a style to one of 'normal', 'italic', 'oblique'. """

	if isinstance(style, bool):
		return STYLE_ITALIC if style else STYLE_NORMAL

	if isinstance(style, str):
		key = style.strip().lower()
		if key in VALID_STYLES:
			return key
		if key in ("roman", "upright", "regular"):
			return STYLE_NORMAL

	warnings.warn(f"Unrecognised font style {style!r}; using '{STYLE_NORMAL}'.")
	return STYLE_NORMAL


def normalize_role(name):
	""" Return the canonical generic role for a name, or None if not a role. """

	if not isinstance(name, str):
		return None
	key = name.strip().lower()
	if key in GENERIC_ROLES:
		return key
	return ROLE_ALIASES.get(key)


def is_generic_role(name):
	return normalize_role(name) is not None


# ==============================================================================
# Font stacks
# ==============================================================================

def normalize_stack(stack):
	"""Coerce a font specification into a clean ordered stack.

	Accepts a single family name (as written by pre-1.0 GrAF and by anyone who
	just wants one font) or an ordered list. Blank entries are dropped and
	duplicates collapsed, preserving order.
	"""

	if stack is None:
		return []

	if isinstance(stack, str):
		candidates = [stack]
	else:
		try:
			candidates = list(stack)
		except TypeError:
			warnings.warn(f"Unusable font specification {stack!r}; ignoring.")
			return []

	cleaned = []
	for entry in candidates:
		if not isinstance(entry, str):
			warnings.warn(f"Ignoring non-string entry {entry!r} in font stack.")
			continue
		name = entry.strip()
		if not name:
			continue
		role = normalize_role(name)
		name = role if role else name
		if name not in cleaned:
			cleaned.append(name)

	return cleaned


def stack_role(stack):
	""" The generic role a stack ends in, or None if it names none. """

	for entry in reversed(normalize_stack(stack)):
		role = normalize_role(entry)
		if role:
			return role
	return None


def ensure_role(stack, role=None):
	"""Return the stack with a generic role guaranteed at the end.

	Every stack GrAF writes ends in a role, so that a reader lacking every named
	family still knows what kind of type the figure was set in.
	"""

	cleaned = normalize_stack(stack)
	if stack_role(cleaned):
		return cleaned

	fallback = normalize_role(role) or LAST_RESORT_ROLE
	return cleaned + [fallback]


# ==============================================================================
# The bundled font manifest
# ==============================================================================

_MANIFEST_FILENAME = "portable_fonts.json"


def _manifest_path(package_dir):
	return os.path.join(package_dir, "assets", _MANIFEST_FILENAME)


def load_manifest(package_dir):
	"""Read portable_fonts.json and resolve every declared face.

	Returns (families, role_defaults). Each family is a dict with 'family',
	'aliases', 'role', 'faces' (a list of resolved face records) and its licence
	metadata. A family whose files are missing is kept but has no usable faces,
	so a broken install degrades rather than exploding at import time.
	"""

	path = _manifest_path(package_dir)

	try:
		with open(path, 'r', encoding='utf-8') as fh:
			data = json.load(fh)
	except Exception as e:
		warnings.warn(
			f"Could not read the GrAF font manifest at '{path}' ({e}). "
			f"Bundled fonts will be unavailable; matplotlib defaults will be used."
		)
		return [], {}

	families = []
	for entry in data.get('families', []):
		family_name = entry.get('family')
		if not family_name:
			warnings.warn("Font manifest contains a family with no 'family' name; skipping.")
			continue

		# A family claiming a generic role as an alias would reintroduce exactly
		# the conflation this module exists to prevent.
		aliases = []
		for alias in entry.get('aliases', []):
			if is_generic_role(alias):
				warnings.warn(
					f"Font family '{family_name}' claims the generic role "
					f"'{alias}' as an alias; ignoring it. Roles are set by the "
					f"'role' field and by role_defaults, not by aliases."
				)
				continue
			aliases.append(alias)

		faces = []
		for face in entry.get('faces', []):
			rel = face.get('file')
			if not rel:
				continue
			face_path = os.path.join(package_dir, *rel)
			if not os.path.isfile(face_path):
				warnings.warn(
					f"Font file declared for '{family_name}' is missing: {face_path}"
				)
				continue
			try:
				props = fm.FontProperties(fname=face_path)
			except Exception as e:
				warnings.warn(f"Could not load font '{face_path}': {e}")
				continue

			faces.append({
				'weight': normalize_weight(face.get('weight', NORMAL_WEIGHT)),
				'style': normalize_style(face.get('style', STYLE_NORMAL)),
				'path': face_path,
				'props': props,
			})

		families.append({
			'family': family_name,
			'aliases': aliases,
			'role': normalize_role(entry.get('role')) or LAST_RESORT_ROLE,
			'faces': faces,
			'license': entry.get('license'),
			'copyright': entry.get('copyright'),
			'source_url': entry.get('source_url'),
			'license_file': entry.get('license_file'),
			'notes': entry.get('notes'),
		})

	role_defaults = {}
	for role, family_name in data.get('role_defaults', {}).items():
		canonical = normalize_role(role)
		if canonical:
			role_defaults[canonical] = family_name
		else:
			warnings.warn(f"Font manifest declares a default for unknown role '{role}'.")

	return families, role_defaults


# ==============================================================================
# User configuration
# ==============================================================================

CONFIG_FILENAME = "fonts.json"


def user_config_dir():
	"""Per-user GrAF config directory.

	Deliberately a plain directory rather than Qt's QSettings: this module must
	work headless, and base.py must not depend on PyQt.
	"""

	if platform.system() == "Windows":
		base = os.environ.get('APPDATA') or os.path.expanduser('~')
	else:
		base = os.environ.get('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config')
	return os.path.join(base, 'graf')


def user_config_path():
	return os.path.join(user_config_dir(), CONFIG_FILENAME)


def load_user_config(path=None):
	"""Read the user's font preferences. Missing or broken config is not fatal.

	Returns a dict with 'defaults' (role -> family), 'font_paths', and 'aliases'.
	"""

	path = path or user_config_path()
	empty = {'defaults': {}, 'font_paths': [], 'aliases': {}}

	if not os.path.isfile(path):
		return empty

	try:
		with open(path, 'r', encoding='utf-8') as fh:
			data = json.load(fh)
	except Exception as e:
		warnings.warn(f"Ignoring unreadable GrAF font config at '{path}': {e}")
		return empty

	if not isinstance(data, dict):
		warnings.warn(f"Ignoring GrAF font config at '{path}': expected an object.")
		return empty

	defaults = {}
	for role, family in (data.get('defaults') or {}).items():
		canonical = normalize_role(role)
		if not canonical:
			warnings.warn(f"Font config sets a default for unknown role '{role}'; ignoring.")
			continue
		if not isinstance(family, str) or not family.strip():
			warnings.warn(f"Font config default for '{role}' is not a family name; ignoring.")
			continue
		defaults[canonical] = family.strip()

	font_paths = []
	for entry in (data.get('font_paths') or []):
		if isinstance(entry, str) and entry.strip():
			font_paths.append(os.path.expanduser(entry.strip()))

	aliases = {}
	for name, target in (data.get('aliases') or {}).items():
		if isinstance(name, str) and isinstance(target, str):
			aliases[name.strip().lower()] = target.strip()

	return {'defaults': defaults, 'font_paths': font_paths, 'aliases': aliases}


def save_user_config(config, path=None):
	""" Write the user's font preferences, creating the config directory. """

	path = path or user_config_path()
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, 'w', encoding='utf-8') as fh:
		json.dump(config, fh, indent=2, sort_keys=True)
		fh.write('\n')
	return path


# ==============================================================================
# The resolver
# ==============================================================================

def _face_score(face, weight, style):
	"""Cost of using `face` for a requested weight/style. Lower is better.

	A simplified CSS font-matching rule: style is nearly categorical (a normal
	face standing in for italic is a visible substitution), weight is a
	distance. Italic and oblique are near-substitutes for each other.
	"""

	if face['style'] == style:
		style_cost = 0
	elif {face['style'], style} == {STYLE_ITALIC, STYLE_OBLIQUE}:
		style_cost = 100
	else:
		style_cost = 2000

	return style_cost + abs(face['weight'] - weight)


def _select_face(faces, weight, style):
	""" Best available face for the requested weight/style, or None. """

	if not faces:
		return None
	return min(faces, key=lambda f: _face_score(f, weight, style))


class FontResolver:
	"""Resolves font stacks against bundled, user-configured and system fonts.

	Held as a single module-level instance (see `resolver` below) so the system
	font list and user config are read once rather than per figure.
	"""

	def __init__(self, package_dir, config_path=None, use_system_fonts=True):
		self.package_dir = package_dir
		self.config_path = config_path
		self.use_system_fonts = use_system_fonts

		self.families = []
		self.role_defaults = {}
		self.config = {'defaults': {}, 'font_paths': [], 'aliases': {}}

		self._by_name = {}			# lower-cased family name/alias -> family
		self._extra_faces = {}		# lower-cased family name -> [face records]
		self._warned = set()		# so a substitution warns once, not per artist

		self.reload()

	# -- loading -------------------------------------------------------------

	def reload(self):
		""" Re-read the bundled manifest, the user config, and extra font paths. """

		self.families, self.role_defaults = load_manifest(self.package_dir)
		self.config = load_user_config(self.config_path)

		self._by_name = {}
		for family in self.families:
			self._by_name[family['family'].lower()] = family
			for alias in family['aliases']:
				self._by_name[alias.lower()] = family

		self._extra_faces = {}
		for directory in self.config['font_paths']:
			self._index_font_path(directory)

		self._warned = set()

	def _index_font_path(self, directory):
		""" Index every font file under a user-configured directory. """

		if not os.path.isdir(directory):
			warnings.warn(f"Configured font path does not exist: {directory}")
			return

		try:
			found = fm.findSystemFonts(fontpaths=[directory])
		except Exception as e:
			warnings.warn(f"Could not scan font path '{directory}': {e}")
			return

		for path in found:
			try:
				props = fm.FontProperties(fname=path)
				name = props.get_name()
			except Exception:
				continue

			self._extra_faces.setdefault(name.lower(), []).append({
				'weight': normalize_weight(_props_weight(props)),
				'style': normalize_style(props.get_style() or STYLE_NORMAL),
				'path': path,
				'props': props,
			})

	# -- lookup --------------------------------------------------------------

	def _resolve_alias(self, name):
		return self.config['aliases'].get(name.strip().lower(), name)

	def family_for_role(self, role):
		""" Concrete family serving a role: user preference first, then bundled. """

		role = normalize_role(role) or LAST_RESORT_ROLE

		configured = self.config['defaults'].get(role)
		if configured:
			return configured

		bundled = self.role_defaults.get(role)
		if bundled:
			return bundled

		# Nothing declared -- take the first bundled family claiming the role.
		for family in self.families:
			if family['role'] == role and family['faces']:
				return family['family']
		return None

	def _lookup_bundled(self, name, weight, style):
		family = self._by_name.get(name.strip().lower())
		if family is None:
			return None
		face = _select_face(family['faces'], weight, style)
		if face is None:
			return None
		return face['props'], family['family']

	def _lookup_extra(self, name, weight, style):
		faces = self._extra_faces.get(name.strip().lower())
		if not faces:
			return None
		face = _select_face(faces, weight, style)
		if face is None:
			return None
		return face['props'], face['props'].get_name()

	def _lookup_system(self, name, weight, style):
		"""Ask matplotlib for a system-installed family.

		fallback_to_default=False is essential: without it matplotlib silently
		returns DejaVu Sans for anything it cannot find, which would make every
		lookup "succeed" and defeat the whole stack.
		"""

		if not self.use_system_fonts:
			return None

		try:
			props = fm.FontProperties(family=name, weight=weight, style=style)
			path = fm.findfont(props, fallback_to_default=False)
		except Exception:
			return None

		if not path or not os.path.isfile(path):
			return None

		try:
			resolved = fm.FontProperties(fname=path)
			return resolved, resolved.get_name()
		except Exception:
			return None

	def _lookup_family(self, name, weight, style):
		""" Bundled -> user-configured paths -> system. First hit wins. """

		name = self._resolve_alias(name)
		for lookup in (self._lookup_bundled, self._lookup_extra, self._lookup_system):
			hit = lookup(name, weight, style)
			if hit is not None:
				return hit
		return None

	# -- the public entry point ---------------------------------------------

	def resolve(self, stack, weight=NORMAL_WEIGHT, style=STYLE_NORMAL, warn=True):
		"""Resolve a font stack to (FontProperties, resolved_family_name).

		Walks the stack in order. A generic role resolves through the user's
		default for that role, then the bundled default. If no entry resolves,
		the stack's trailing role decides -- so a serif request degrades to
		another serif rather than jumping font class.

		Returns (None, "") when nothing at all can be resolved, which tells the
		caller to leave matplotlib's own default in place.
		"""

		weight = normalize_weight(weight)
		style = normalize_style(style)
		candidates = normalize_stack(stack)

		for index, entry in enumerate(candidates):
			role = normalize_role(entry)
			if role:
				family_name = self.family_for_role(role)
				if not family_name:
					continue
				hit = self._lookup_family(family_name, weight, style)
			else:
				hit = self._lookup_family(entry, weight, style)

			if hit is not None:
				props, resolved = hit
				# Only a genuine substitution is worth reporting. Matching the
				# author's first choice is not one -- however it matched, whether
				# by canonical name, a bundled alias ('mfb' -> MFB Oldstyle), or
				# an alias the user configured themselves. Warning on those
				# would cry wolf on the system working exactly as intended.
				if warn and index > 0:
					self._warn_once(candidates[0], resolved)
				return props, resolved

		# Nothing in the stack resolved -- fall back within the right font class.
		role = stack_role(candidates) or LAST_RESORT_ROLE
		family_name = self.family_for_role(role)
		if family_name:
			hit = self._lookup_family(family_name, weight, style)
			if hit is not None:
				props, resolved = hit
				if warn and candidates:
					self._warn_once(candidates[0], resolved, role=role)
				return props, resolved

		if warn and candidates:
			self._warn_once(candidates[0], "the matplotlib default")
		return None, ""

	def _warn_once(self, requested, used, role=None):
		key = (str(requested), str(used))
		if key in self._warned:
			return
		self._warned.add(key)

		via = f" (via the '{role}' role)" if role else ""
		warnings.warn(
			f"Font '{requested}' is not available on this machine; using "
			f"'{used}'{via}. The figure's data and layout are unaffected, only "
			f"its typeface. Set a preferred family with "
			f"graf.set_font_default(), or add a font path to "
			f"{user_config_path()}."
		)

	# -- introspection -------------------------------------------------------

	def available_families(self, include_system=False):
		""" Family names this installation can resolve. """

		names = [f['family'] for f in self.families if f['faces']]
		names += sorted(self._extra_faces)

		if include_system and self.use_system_fonts:
			try:
				names += sorted({f.name for f in fm.fontManager.ttflist})
			except Exception:
				pass

		seen, unique = set(), []
		for name in names:
			if name.lower() not in seen:
				seen.add(name.lower())
				unique.append(name)
		return unique

	def describe_roles(self):
		""" Which concrete family currently serves each generic role. """

		return {role: self.family_for_role(role) for role in GENERIC_ROLES}


def _props_weight(props):
	""" matplotlib returns weights as either an int or a name. """

	try:
		return props.get_weight()
	except Exception:
		return NORMAL_WEIGHT


# ==============================================================================
# Module-level resolver and the user-facing preference API
# ==============================================================================

resolver = None			# initialised by init_resolver(), called from base.py


def init_resolver(package_dir, config_path=None, use_system_fonts=True):
	global resolver
	resolver = FontResolver(package_dir, config_path=config_path,
							use_system_fonts=use_system_fonts)
	return resolver


def resolve_font(stack, weight=NORMAL_WEIGHT, style=STYLE_NORMAL, warn=True):
	""" Resolve a font stack. See FontResolver.resolve. """

	if resolver is None:
		raise RuntimeError("GrAF font resolver is not initialised.")
	return resolver.resolve(stack, weight=weight, style=style, warn=warn)


def set_font_default(role, family, persist=True):
	"""Choose the family that serves a generic role on this machine.

	    graf.set_font_default('serif', 'EB Garamond')

	Affects every GrAF figure that asks for that role, including files written
	elsewhere -- which is the point: the file states intent, the machine states
	preference.
	"""

	canonical = normalize_role(role)
	if canonical is None:
		raise ValueError(
			f"Unknown font role {role!r}. Valid roles: {', '.join(GENERIC_ROLES)}."
		)
	if not isinstance(family, str) or not family.strip():
		raise ValueError("Font family must be a non-empty string.")

	family = family.strip()

	if resolver is not None:
		resolver.config['defaults'][canonical] = family
		resolver._warned = set()

	if persist:
		path = resolver.config_path if resolver else None
		stored = load_user_config(path)
		stored['defaults'][canonical] = family
		save_user_config(stored, path)

	return family


def get_font_defaults():
	""" The concrete family currently serving each generic role. """

	if resolver is None:
		raise RuntimeError("GrAF font resolver is not initialised.")
	return resolver.describe_roles()


def add_font_path(directory, persist=True):
	""" Add a directory of fonts for GrAF to search, and index it now. """

	directory = os.path.expanduser(str(directory))
	if not os.path.isdir(directory):
		raise ValueError(f"Not a directory: {directory}")

	if resolver is not None:
		if directory not in resolver.config['font_paths']:
			resolver.config['font_paths'].append(directory)
		resolver._index_font_path(directory)
		resolver._warned = set()

	if persist:
		path = resolver.config_path if resolver else None
		stored = load_user_config(path)
		if directory not in stored['font_paths']:
			stored['font_paths'].append(directory)
		save_user_config(stored, path)

	return directory


def available_font_families(include_system=False):
	""" Family names this installation can resolve. """

	if resolver is None:
		raise RuntimeError("GrAF font resolver is not initialised.")
	return resolver.available_families(include_system=include_system)
