import destinationCsv from "../../backend/tests/fixtures/destination.csv?raw";
import sourceCsv from "../../backend/tests/fixtures/source.csv?raw";

export function demoFile(kind: "source" | "destination"): File {
  return new File(
    [kind === "source" ? sourceCsv : destinationCsv],
    `${kind}.csv`,
    { type: "text/csv" },
  );
}
