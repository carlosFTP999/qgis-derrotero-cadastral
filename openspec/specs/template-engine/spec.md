# Template Engine Specification

## Purpose

Provide a sandboxed Jinja2 environment that loads templates from built-in and user folders, registers custom derrotero filters, and exposes DSL variables for blueprint rendering.

## Requirements

### R-TE-01: Sandboxed environment

The engine MUST use Jinja2's SandboxedEnvironment. The set of accessible builtins SHALL be restricted to a minimal whitelist. File system access from inside a template SHALL be denied.

#### Scenario: safe template
- GIVEN a simple template with variable substitution
- WHEN the template is parsed
- THEN rendering proceeds without error

#### Scenario: blocked filesystem
- GIVEN a template containing open('/etc/passwd')
- WHEN the template is executed
- THEN a security error SHALL be raised

### R-TE-02: Custom filter registration

The engine MUST register the following custom filters for use in templates:
- to_dms: number to DMS string
- to_quadrant: azimuth to quadrant bearing
- format_number: decimal precision
- to_cardinal: azimuth to cardinal orientation

#### Scenario: to_dms filter
- GIVEN a template using {{ value|to_dms(2) }}
- WHEN the filter is applied to 45.5
- THEN the result SHALL be "45° 30' 00.00\""

### R-TE-03: Load paths

Templates SHALL be loaded from two sources: a built-in directory (resources/templates/) and a user directory (~/.local/share/QGIS/.../derrotero/templates/). The user path SHALL take precedence over built-in.

### R-TE-04: Initial blueprints

The built-in set SHALL include at three blueprints:
- ES clásico: Spanish standard format
- LADM-COL: Colombian LADM format
- Tabla compacta (generic)

Each SHOULD be complete enough to generate a TXT derrotero.

### R-TE-05: DSL variable error

If a template references a variable not present in the passed dict and without a Jinja2 default, the engine SHALL raise an error.

#### Scenario: missing variable
- GIVEN a template referencing {{ azimutt }} (typo)
- WHEN rendered without default
- THEN an UndefinedError is raised

### EV-01: malformed template
- GIVEN a user-supplied template with syntax error
- WHEN loaded
- THEN an informative error with line number is reported

### EV-02: template not found
- GIVEN a non-existent identifier
- WHEN a blueprint is loaded
- THEN a TemplateNotFound error is raised
