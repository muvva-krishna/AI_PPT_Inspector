def write_report(results, total_slides, output_path="reports.txt"):
    """
    Writes findings to the given output_path.
    results: dict with "issues" and "suggestions".
    """
    with open(output_path, "w", encoding="utf-8") as f:
        if not results or not results.get("issues"):
            f.write(f"No issues found across {total_slides}/{total_slides} slides.\n\n")
        else:
            f.write("Detected Issues:\n")
            for issue in results.get("issues", []):
                slides_str = ", ".join(map(str, issue.get("slides", [])))
                f.write(f"- Slides {slides_str}: {issue.get('description', '')}\n")
                f.write(f"  Suggestion: {issue.get('suggestion', '')}\n\n")

        f.write("\nSuggestions:\n")
        for sug in results.get("suggestions", []) if results else []:
            f.write(f"- {sug}\n")
