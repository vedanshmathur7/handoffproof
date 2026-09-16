# Synthetic reconciliation fixtures

All people, companies, IDs, and timestamps here are invented test data.

- `source.csv`: six valid source records, one for every result category.
- `destination.csv`: complete destination data for matched, duplicate, and mismatch cases.
- `partial_destination.csv`: deliberately incomplete coverage for the unknown case.
- `malformed_source.csv`: rejected-row examples for parser tests in Task 03.
- `fixture_manifest.json`: frozen expected category and reason for every valid source ID.

## CSV contracts

Source headers:

`source_record_id,submitted_at,email,full_name,company,region,transfer_enabled`

Destination headers:

`destination_record_id,created_at,email,full_name,company,region`
