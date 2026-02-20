#!/usr/bin/env python3
"""
Bank/Credit Card Statement Transaction Extractor v5
Extracts from: HSBC, SC Credit, EarnMore, Mox, WeLab, ZA, FUTU, Webull
"""

import pdfplumber
import csv
import re
from pathlib import Path

def extract_hsbc(pdf_path):
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages])
        lines = full_text.split('\n')
        current_date = ""
        
        for line in lines:
            date_match = re.match(r'^(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s', line, re.IGNORECASE)
            if date_match:
                current_date = date_match.group(1)
            if not current_date:
                continue
            if any(x in line.upper() for x in ['BALANCE', 'RELATIONSHIP', 'SAVINGS', 'FOREIGN', 'CCY', 'TOTAL']):
                continue
            
            keywords = ['SALARY', 'ATM', 'FUTU', 'WEBULL', 'OGILVY', 'KREW', 'DBS', 'INTERACTIVE', 'CHAPS', 'TRANSFER', 'CREDIT INTEREST']
            if any(kw in line.upper() for kw in keywords):
                amounts = re.findall(r'([\d,]+\.\d{2})', line)
                if amounts:
                    amount = float(amounts[0].replace(',', ''))
                    if amount > 100:
                        desc = re.sub(r'^' + str(current_date) + r'\s*', '', line)
                        desc = re.sub(r'[\d,]+\.\d{2}.*$', '', desc).strip()[:60]
                        is_credit = any(kw in line.upper() for kw in ['SALARY', 'KREW', 'OGILVY']) and 'DEBIT' not in line.upper()
                        if desc and len(desc) > 2:
                            transactions.append({
                                'Date': current_date, 'Account': 'HSBC', 'Type': 'Credit' if is_credit else 'Debit',
                                'Description': desc, 'Vendor': desc[:40], 'Amount': amount if is_credit else -amount, 'Currency': 'HKD'
                            })
    return transactions

def extract_sc_credit(pdf_path):
    """SC Credit / EarnMore / similar formats"""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    row_text = ' '.join([str(c) for c in row if c])
                    date_match = re.search(r'(\d{1,2}月\d{1,2}日)', row_text)
                    if not date_match:
                        continue
                    date = date_match.group(1)
                    amount_match = re.search(r'(\d+[\d,]+\.\d{2})(?:\s|$)', row_text)
                    if amount_match:
                        try:
                            amount = float(amount_match.group(1).replace(',', ''))
                            if amount > 100 and 'P2*' not in row_text:
                                desc = row_text
                                desc = re.sub(r'\d{1,2}月\d{1,2}日', '', desc)
                                desc = re.sub(r'\d+[\d,]+\.\d{2}', '', desc)
                                desc = re.sub(r'Transaction Ref.*', '', desc).strip()[:60]
                                if desc and len(desc) > 2:
                                    transactions.append({
                                        'Date': date, 'Account': 'SC Credit', 'Type': 'Debit',
                                        'Description': desc, 'Vendor': desc[:40], 'Amount': -abs(amount), 'Currency': 'HKD'
                                    })
                        except:
                            pass
    return transactions

def extract_mox(pdf_path):
    """Mox Credit Card"""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    row_text = ' '.join([str(c) for c in row if c])
                    
                    # Look for date and amount
                    date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)', row_text, re.IGNORECASE)
                    if not date_match:
                        continue
                    date = date_match.group(1)
                    
                    # Find amount (negative = spending)
                    amount_match = re.search(r'(-?[\d,]+\.\d{2})\s*HKD', row_text)
                    if amount_match:
                        try:
                            amount_str = amount_match.group(1).replace(',', '')
                            if amount_str.startswith('-'):
                                amount = float(amount_str.replace('-', ''))
                                if amount > 10:
                                    desc = row_text
                                    desc = re.sub(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', '', desc)
                                    desc = re.sub(r'-?[\d,]+\.\d{2}.*HKD', '', desc).strip()[:60]
                                    if desc and len(desc) > 2:
                                        transactions.append({
                                            'Date': date, 'Account': 'Mox', 'Type': 'Debit',
                                            'Description': desc, 'Vendor': desc[:40], 'Amount': -abs(amount), 'Currency': 'HKD'
                                        })
                        except:
                            pass
    return transactions

def extract_za(pdf_path):
    """ZA Bank"""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages])
        lines = full_text.split('\n')
        
        for line in lines:
            # Look for transaction lines: "01 Feb 2025 Interest 0.02"
            match = re.match(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s+(\w+.*?)\s+([\d,]+\.\d{2})', line, re.IGNORECASE)
            if match:
                date = match.group(1)
                desc = match.group(2).strip()[:50]
                amount = float(match.group(3).replace(',', ''))
                
                # Skip balance lines
                if any(x in desc.upper() for x in ['BALANCE', 'OPENING', 'CLOSING', 'TOTAL']):
                    continue
                
                if amount > 0 and desc:
                    transactions.append({
                        'Date': date, 'Account': 'ZA Bank', 'Type': 'Credit',
                        'Description': desc, 'Vendor': desc[:40], 'Amount': amount, 'Currency': 'HKD'
                    })
                elif amount > 0:
                    transactions.append({
                        'Date': date, 'Account': 'ZA Bank', 'Type': 'Debit',
                        'Description': desc, 'Vendor': desc[:40], 'Amount': -amount, 'Currency': 'HKD'
                    })
    return transactions

def extract_welab(pdf_path):
    """WeLab Bank"""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages])
        lines = full_text.split('\n')
        
        for line in lines:
            # Pattern: "01 Jun 2025 Receive money from MR WONG LIK 1.00"
            match = re.match(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s+(.*?)\s+(-?[\d,]+\.\d{2})', line, re.IGNORECASE)
            if match:
                date = match.group(1)
                desc = match.group(2).strip()[:50]
                amount_str = match.group(3).replace(',', '')
                
                # Skip balance lines
                if any(x in desc.upper() for x in ['BALANCE', 'OPENING', 'CLOSING', '承上結餘', '戶口結餘']):
                    continue
                
                try:
                    amount = float(amount_str)
                    if amount > 0 and 'Balance' not in desc:
                        transactions.append({
                            'Date': date, 'Account': 'WeLab', 'Type': 'Credit' if amount > 0 else 'Debit',
                            'Description': desc, 'Vendor': desc[:40], 'Amount': amount, 'Currency': 'HKD'
                        })
                    elif amount < 0:
                        transactions.append({
                            'Date': date, 'Account': 'WeLab', 'Type': 'Debit',
                            'Description': desc, 'Vendor': desc[:40], 'Amount': amount, 'Currency': 'HKD'
                        })
                except:
                    pass
    return transactions

def extract_futu(pdf_path):
    """FUTU - basic"""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages])
        for match in re.finditer(r'(\d{4}-\d{2}-\d{2}).*?(Deposit|Withdraw|Buy|Sell).*?([\d,]+\.\d{2})', full_text):
            date, desc, amt = match.groups()
            amount = float(amt.replace(',', ''))
            is_credit = 'Deposit' in desc
            transactions.append({
                'Date': date, 'Account': 'FUTU', 'Type': 'Credit' if is_credit else 'Debit',
                'Description': desc, 'Vendor': 'FUTU', 'Amount': amount if is_credit else -amount, 'Currency': 'HKD'
            })
    return transactions

def extract_webull(pdf_path):
    """Webull - basic"""
    return extract_futu(pdf_path)  # Similar format

EXTRACTORS = {
    'hsbc': extract_hsbc,
    'sc_credit': extract_sc_credit,
    'earnmore': extract_sc_credit,
    'mox': extract_mox,
    'za': extract_za,
    'za_bank': extract_za,
    'welab': extract_welab,
    'futu': extract_futu,
    'webull': extract_webull,
}

def detect_account(filename):
    fn = filename.lower()
    if 'hsbc' in fn: return 'hsbc'
    elif 'sc_' in fn or 'sc credit' in fn: return 'sc_credit'
    elif 'earnmore' in fn: return 'earnmore'
    elif 'mox' in fn: return 'mox'
    elif 'welab' in fn: return 'welab'
    elif 'za' in fn and 'bank' in fn: return 'za_bank'
    elif 'za' in fn: return 'za'
    elif 'futu' in fn: return 'futu'
    elif 'webull' in fn: return 'webull'
    elif 'ibkr' in fn: return 'ibkr'
    return 'unknown'

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract transactions to CSV')
    parser.add_argument('input_dir')
    parser.add_argument('output_csv')
    args = parser.parse_args()
    
    with open(args.output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date','Account','Type','Description','Vendor','Amount','Currency'])
        writer.writeheader()
        
        total = 0
        for pdf_file in sorted(Path(args.input_dir).glob('*.pdf')):
            account_type = detect_account(pdf_file.name)
            print(f"Processing: {pdf_file.name} ({account_type})")
            
            if account_type in EXTRACTORS:
                try:
                    txns = EXTRACTORS[account_type](str(pdf_file))
                    for txn in txns:
                        writer.writerow(txn)
                        total += 1
                        print(f"  {txn['Date']}: {txn['Type']} {txn['Amount']} = {txn['Description'][:30]}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            else:
                print(f"  ⚠️ Unsupported: {account_type}")
    
    print(f"\n✓ Total: {total} transactions -> {args.output_csv}")

if __name__ == '__main__':
    main()
