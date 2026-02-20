# Bank Statement Transaction Extractor

Extracts transactions from bank/credit card PDF statements to CSV.

## Supported Accounts
- HSBC ✅
- SC Credit ✅
- EarnMore ✅
- FUTU ⚠️ (basic)
- Webull ⚠️ (basic)
- Mox, WeLab, ZA: Coming soon

## Usage
```bash
python3 extract_transactions.py /path/to/pdfs output.csv
```

## Output Format
| Column | Description |
|--------|-------------|
| Date | Transaction date |
| Account | Bank/CC name |
| Type | Credit/Debit |
| Description | Transaction description |
| Vendor | Merchant name |
| Amount | Transaction amount |
| Currency | HKD/USD |

## Requirements
- Python 3
- pdfplumber
