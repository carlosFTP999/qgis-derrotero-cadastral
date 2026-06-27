# Derrotero Generation Specification

## Purpose

Orchestrate the final step of the pipeline: combine vertex extraction, bearing/distance calculation, and colindancia detection to produce a plain text file rendered via a selected Jinja2 blueprint.

## Requirements

### R-DG-01: Blueprint selection

The system SHALL offer the user a choice of loaded blueprints (built-in and user). The default SHOULD be ES clásico.

#### Scenario: select blueprint
- GIVEN four available blueprints
- WHEN the user selects "ES clásico"
- THEN that template is loaded for rendering

### R-DG-02: Full DSL variable injection

Before rendering, the system MUST replace all DSL variables in the selected template with their computed values. Variables originate from vertex extraction, bearing and distance engine, colindancia detection, and parcel layer attributes.

#### Scenario: two-segment parcel
- GIVEN a single completed pipeline run with two extracted segments
- WHEN the template is rendered
- THEN the output text contains actual bearing, distance, and colindancia for segment V1-V2

### R-DG-03: TXT output

The final output MUST be a plain text string with newline breaks. It SHALL be suitable for display in a QPlainTextEdit preview.

#### Scenario: preview update
- GIVEN a rendered derrotero as a string
- WHEN the preview widget is updated
- THEN the widget displays the rendered plain text without markup

### R-DG-04: File export

The user SHALL be able to save the generated text to a .txt file. The default filename SHOULD be parcel-fid_derrotero.txt.

#### Scenario: export dialog
- GIVEN a rendered derrotero
- WHEN the user clicks export
- THEN a QFileDialog opens with the default filename
- AND clicking save persists the content to disk

### EV-01: zero segments
- GIVEN a parcel with no extracted segments (NULL geometry)
- WHEN generation is attempted
- THEN a warning message is shown instead of an empty output

### EV-02: rendering error
- GIVEN a template that fails during rendering
- WHEN generation is attempted
- THEN the error is caught and reported to the user
- AND no partial output is produced
