# Decisions

## Worksheet, not a message
ABF publishes CUSDEC / IMD message guides for software developers. Sending one of those needs a registered client, certificates, and a licensed declaration. Copying a subset of public N10 captions into a review file is the piece that removes rekeying without pretending to be a cargo system.

## Tariff column stays empty
A printed HS code is copied into `hs_code_as_printed`. `tariff_classification` is always null so a CSV export cannot be mistaken for a classified entry.

## Consignee is labelled, not trusted
The header field is `importer_name` because that is the N10 idea, and `sources` records that the value came from `consignee.name`. The gaps list says the consignee may be a notify party.
