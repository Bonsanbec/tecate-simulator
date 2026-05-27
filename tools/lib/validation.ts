export interface ValidationIssue {
  severity: "error" | "warning";
  message: string;
  file?: string;
}

export function addError(issues: ValidationIssue[], message: string, file?: string): void {
  issues.push(file === undefined
    ? { severity: "error", message }
    : { severity: "error", message, file });
}

export function addWarning(issues: ValidationIssue[], message: string, file?: string): void {
  issues.push(file === undefined
    ? { severity: "warning", message }
    : { severity: "warning", message, file });
}

export function printIssues(title: string, issues: ValidationIssue[]): void {
  console.log(title);

  if (issues.length === 0) {
    console.log("OK");
    return;
  }

  for (const issue of issues) {
    const location = issue.file ? ` ${issue.file}` : "";
    console.log(`${issue.severity.toUpperCase()}:${location} ${issue.message}`);
  }
}

export function failOnErrors(issues: ValidationIssue[]): void {
  if (issues.some((issue) => issue.severity === "error")) {
    process.exitCode = 1;
  }
}
