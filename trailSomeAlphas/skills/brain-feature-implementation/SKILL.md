---
name: brain-feature-implementation
description: Automate conversion of Brain idea documents into actionable Alpha expressions using local CSV data.
---

# Brain Feature Implementation

## Description
This skill automates the process of converting a WorldQuant Brain idea document (Markdown) into actionable Alpha expressions.

## Instructions

1.  **Analyze the Idea Document**
    *   Read the provided markdown file.
    *   Extract the following metadata:
        *   **Dataset ID** (e.g., `analyst15`)
        *   **Region** (e.g., `GLB`)
        *   **Delay** (e.g., `1` or `0`)
    *   *If any metadata is missing, ask the user to clarify.*

2.  **Plan Implementation**
    *   Scan the markdown file for **Feature Definitions** or **Formulas**.
    *   Look for patterns like `Definition: <formula>` or code blocks describing math.
    *   Use the `manage_todo_list` tool to create a plan with one entry for each unique idea/formula found.
        *   *Title*: The Idea Name or ID (e.g., "3.1.1 Estimate Stability Score").
        *   *Description*: The specific template formula (e.g., `template: "{st_dev} / abs({mean})"`).

3.  **Execute Implementation**
    *   For each item in the Todo List:
        *   **Construct the Template**:
            *   Use Python format string syntax `{variable}`.
            *   The `{variable}` must match the **suffix** of the fields in the dataset (e.g., `mean`, `st_dev`, `gro`).
            *   **CRITICAL**: Do NOT include the full prefix or horizon in the template. The script auto-detects these.
            *   *Correct Example*: For `anl15_gr_12_m_gro / anl15_gr_12_m_pe`, use template: `{gro} / {pe}`.
            *   *Incorrect Example*: `{anl15_gr_12_m_gro} / {pe}` (Includes prefix).
            *   *Incorrect Example*: `${gro} / ${pe}` (Shell syntax).
            *   *Note*: The script ONLY accepts `--template` and `--dataset`. Do not pass any other arguments like `--filters` or `--groupby`.
        *   Verify the output (number of expressions generated).
        *   Mark the Todo item as completed.

