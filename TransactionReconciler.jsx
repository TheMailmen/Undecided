import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";

// ─── Constants ───────────────────────────────────────────────────────────────

const GL_ACCOUNTS = {
  "6002": "PAYROLL", "6003": "Advertising", "6062": "Mileage",
  "6071": "Carpet Cleaning", "6072": "Janitorial Expense",
  "6073": "General Maintenance Labor", "6074": "Landscaping",
  "6075": "HOA Dues", "6076": "Cleaning and Maintenance -Other",
  "6077": "Common Area Cleaning", "6078": "Pest Control",
  "6091": "Property Insurance", "6101": "Legal", "6102": "Accounting",
  "6103": "Other", "6104": "Title Fees", "6105": "Security Service",
  "6106": "Bank Fees", "6107": "AUTO AND TRAVEL", "6108": "Meals",
  "6111": "Management Fees", "6112": "Commissions/Placement Fees",
  "6119": "Mortgage Principal", "6121": "Mortgage Interest",
  "6124": "Loan Origination Fee", "6130": "Other interest",
  "6141": "Painting", "6142": "Plumbing", "6143": "Flooring",
  "6144": "HVAC (Heat, Ventilation, Air)", "6145": "Key/Lock Replacement",
  "6146": "Roof Repair", "6147": "Repairs - Other", "6150": "Supplies",
  "6161": "Property Tax", "6162": "Rental Tax Authority",
  "6171": "Electricity", "6172": "Gas", "6173": "Water", "6174": "Sewer",
  "6175": "Garbage and Recycling", "6176": "Internet",
  "6179": "Asset Management Fee", "6180": "Depreciation Expense",
  "6193": "Equipment Rental", "7010": "Appliances",
  "7020": "Equipment/Tools", "7030": "Remodel", "7040": "New Roof",
  "7050": "Furniture", "7060": "Labor", "7070": "Flooring (Capex)",
  "7080": "Hardware", "7090": "Cabinets", "7100": "Supplies (Capex)",
  "7110": "Paint", "7120": "Tub Reglazing",
};

const GL_OPTIONS = Object.entries(GL_ACCOUNTS).map(([code, name]) => ({
  code, name, label: `${code}: ${name}`,
}));

const PROPERTIES = [
  "Granite City",
  "The Groves Apartments - 6800",
  "The Groves Apartments - 6804",
  "The Groves Apartments - 6806",
  "The Groves Apartments - 6808",
  "The Groves Apartments - 6810",
  "The Groves Apartments Leasing Office",
  "Stone Arch Accounting Property",
];

const CASH_ACCOUNTS = [
  "AMEX",
  "AMEX - Groves (Purple)",
  "SAH - Asset Mgmt (Chase)",
  "SAH - GC APTS",
  "SAH - Groves Apts",
  "The Groves Apts LP L.L.C",
];

const DEFAULT_VENDOR_RULES = [
  { pattern: "ZILLOW", vendor: "Zillow Rentals", glCode: "6003", glName: "Advertising", confidence: "High" },
  { pattern: "ACE SOLID WASTE", vendor: "Ace Solid Waste, Inc", glCode: "6175", glName: "Garbage and Recycling", confidence: "High" },
  { pattern: "DOLLARTREE|DOLLAR TREE", vendor: "Dollar Tree", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "SUBWAY", vendor: "Subway", glCode: "6108", glName: "Meals", confidence: "High" },
  { pattern: "SMARTSHEET", vendor: "Smartsheet", glCode: "6103", glName: "Other", confidence: "Medium" },
  { pattern: "AMAZON", vendor: "Amazon", glCode: "6150", glName: "Supplies", confidence: "Medium" },
  { pattern: "GRANITE CITY APARTME", vendor: "The Groves Managment LLC", glCode: "6111", glName: "Management Fees", confidence: "Medium" },
  { pattern: "EXPENSIFY", vendor: "EXPENSIFY, INC.", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "MENARDS", vendor: "Menards", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "HOME DEPOT", vendor: "The Home Depot", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "LOWES|LOWE'S", vendor: "Lowes", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "RODDY", vendor: "RB Construction Services, LLC", glCode: "6175", glName: "Garbage and Recycling", confidence: "Medium" },
  { pattern: "SUNDBERG", vendor: "Sundberg America", glCode: "6150", glName: "Supplies", confidence: "Medium" },
  { pattern: "XCEL ENERGY", vendor: "Xcel Energy", glCode: "6171", glName: "Electricity", confidence: "High" },
  { pattern: "CENTERPOINT", vendor: "CenterPoint Energy", glCode: "6172", glName: "Gas", confidence: "High" },
  { pattern: "COMCAST|XFINITY", vendor: "Comcast Business", glCode: "6176", glName: "Internet", confidence: "High" },
  { pattern: "SHERWIN", vendor: "Sherwin Williams", glCode: "6141", glName: "Painting", confidence: "High" },
  { pattern: "ORKIN|TERMINIX", vendor: "Adams Pest Control, Inc.", glCode: "6078", glName: "Pest Control", confidence: "High" },
  { pattern: "ADAMS PEST", vendor: "Adams Pest Control, Inc.", glCode: "6078", glName: "Pest Control", confidence: "High" },
  { pattern: "FASTSIGNS", vendor: "Fastsigns", glCode: "6003", glName: "Advertising", confidence: "High" },
  { pattern: "ULINE", vendor: "Uline", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "HD SUPPLY", vendor: "HD Supply", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "PARK SUPPLY", vendor: "Park Supply of Minneapolis", glCode: "6142", glName: "Plumbing", confidence: "High" },
  { pattern: "MAPLE GROVE LOCK", vendor: "Maple Grove Lock & Safe", glCode: "6145", glName: "Key/Lock Replacement", confidence: "High" },
  { pattern: "PIPERIGHT", vendor: "Piperight Plumbing, Inc", glCode: "6142", glName: "Plumbing", confidence: "High" },
  { pattern: "SURFACE RENEW", vendor: "Surface Renew", glCode: "7120", glName: "Tub Reglazing", confidence: "High" },
  { pattern: "SUMMIT FIRE", vendor: "Summit Fire Protection", glCode: "6147", glName: "Repairs - Other", confidence: "High" },
  { pattern: "DORGLASS", vendor: "Dorglass, Inc", glCode: "6147", glName: "Repairs - Other", confidence: "High" },
  { pattern: "BATTERIES", vendor: "Batteries & Bulbs", glCode: "6150", glName: "Supplies", confidence: "High" },
  { pattern: "PROSOURCE", vendor: "Prosource Cabinet Division", glCode: "7090", glName: "Cabinets", confidence: "High" },
  { pattern: "CANTARERO", vendor: "Cantarero Flooring LLC", glCode: "6143", glName: "Flooring", confidence: "High" },
  { pattern: "REFERRAL CARPET", vendor: "Referral Carpet and Floor Services", glCode: "6143", glName: "Flooring", confidence: "High" },
  { pattern: "LANO EQUIPMENT", vendor: "Lano Equipment", glCode: "6193", glName: "Equipment Rental", confidence: "High" },
  { pattern: "AUTOPAY PAYMENT|PAYMENT.*THANK", vendor: "__EXCLUDE__", glCode: "__EXCLUDE__", glName: "", confidence: "Auto" },
  { pattern: "KWIK TRIP", vendor: "Kwik Trip", glCode: "6108", glName: "Meals", confidence: "High" },
  { pattern: "MCDONALDS|CHICK-FIL|CHIPOTLE|DOOR DASH", vendor: "Meals", glCode: "6108", glName: "Meals", confidence: "High" },
  { pattern: "CANVA", vendor: "Canva", glCode: "6003", glName: "Advertising", confidence: "High" },
  { pattern: "QUICKBOOKS", vendor: "Quickbooks", glCode: "6102", glName: "Accounting", confidence: "High" },
  { pattern: "TRACK 1099", vendor: "Track 1099", glCode: "6102", glName: "Accounting", confidence: "High" },
];

const DEFAULT_SETTINGS = {
  propertyCode: "Granite City",
  cashAccount: "AMEX",
};

// ─── Styles ──────────────────────────────────────────────────────────────────

const colors = {
  bg: "#0d1117",
  bgCard: "#161b22",
  bgHover: "#1c2333",
  bgInput: "#0d1117",
  border: "#30363d",
  borderFocus: "#58a6ff",
  text: "#e6edf3",
  textMuted: "#8b949e",
  textDim: "#484f58",
  accent: "#58a6ff",
  accentHover: "#79c0ff",
  green: "#238636",
  greenBg: "#0d2818",
  greenText: "#3fb950",
  yellow: "#9e6a03",
  yellowBg: "#2d1f00",
  yellowText: "#d29922",
  red: "#da3633",
  redBg: "#2d0f0e",
  redText: "#f85149",
  grayBg: "#1a1e24",
  grayText: "#6e7681",
};

const s = {
  app: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    color: colors.text,
    backgroundColor: colors.bg,
    minHeight: "100vh",
    fontSize: "14px",
    lineHeight: "1.5",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 24px",
    backgroundColor: colors.bgCard,
    borderBottom: `1px solid ${colors.border}`,
    position: "sticky",
    top: 0,
    zIndex: 100,
  },
  navBrand: {
    fontSize: "16px",
    fontWeight: 600,
    color: colors.text,
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  navTabs: {
    display: "flex",
    gap: "4px",
  },
  navTab: (active) => ({
    padding: "8px 16px",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
    backgroundColor: active ? colors.accent : "transparent",
    color: active ? "#fff" : colors.textMuted,
    transition: "all 0.15s",
  }),
  badge: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minWidth: "20px",
    height: "20px",
    padding: "0 6px",
    borderRadius: "10px",
    fontSize: "11px",
    fontWeight: 600,
    backgroundColor: colors.accent,
    color: "#fff",
    marginLeft: "6px",
  },
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "24px",
  },
  card: {
    backgroundColor: colors.bgCard,
    border: `1px solid ${colors.border}`,
    borderRadius: "8px",
    padding: "24px",
    marginBottom: "16px",
  },
  h2: {
    fontSize: "20px",
    fontWeight: 600,
    marginBottom: "16px",
    color: colors.text,
  },
  h3: {
    fontSize: "16px",
    fontWeight: 600,
    marginBottom: "12px",
    color: colors.text,
  },
  label: {
    display: "block",
    fontSize: "12px",
    fontWeight: 500,
    color: colors.textMuted,
    marginBottom: "6px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  input: {
    width: "100%",
    padding: "8px 12px",
    backgroundColor: colors.bgInput,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
  },
  select: {
    width: "100%",
    padding: "8px 12px",
    backgroundColor: colors.bgInput,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
    appearance: "auto",
  },
  textarea: {
    width: "100%",
    padding: "12px",
    backgroundColor: colors.bgInput,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    fontSize: "13px",
    fontFamily: "monospace",
    outline: "none",
    resize: "vertical",
    boxSizing: "border-box",
  },
  btn: (variant = "primary") => {
    const base = {
      padding: "8px 16px",
      border: "none",
      borderRadius: "6px",
      cursor: "pointer",
      fontSize: "13px",
      fontWeight: 500,
      transition: "all 0.15s",
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
    };
    if (variant === "primary") return { ...base, backgroundColor: colors.accent, color: "#fff" };
    if (variant === "success") return { ...base, backgroundColor: colors.green, color: "#fff" };
    if (variant === "danger") return { ...base, backgroundColor: colors.red, color: "#fff" };
    if (variant === "ghost") return { ...base, backgroundColor: "transparent", color: colors.textMuted, border: `1px solid ${colors.border}` };
    return base;
  },
  dropzone: (dragging) => ({
    border: `2px dashed ${dragging ? colors.accent : colors.border}`,
    borderRadius: "8px",
    padding: "48px 24px",
    textAlign: "center",
    cursor: "pointer",
    backgroundColor: dragging ? "rgba(88,166,255,0.05)" : "transparent",
    transition: "all 0.2s",
  }),
  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
  th: {
    textAlign: "left",
    padding: "10px 12px",
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    color: colors.textMuted,
    borderBottom: `1px solid ${colors.border}`,
    whiteSpace: "nowrap",
  },
  td: {
    padding: "10px 12px",
    fontSize: "13px",
    borderBottom: `1px solid ${colors.border}`,
    verticalAlign: "top",
  },
  mono: {
    fontFamily: "'SF Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
  },
  confidenceBadge: (level) => {
    const map = {
      High: { bg: colors.greenBg, color: colors.greenText, border: colors.green },
      Medium: { bg: colors.yellowBg, color: colors.yellowText, border: colors.yellow },
      Unmatched: { bg: colors.redBg, color: colors.redText, border: colors.red },
      Auto: { bg: colors.grayBg, color: colors.grayText, border: colors.textDim },
    };
    const c = map[level] || map.Unmatched;
    return {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "12px",
      fontSize: "11px",
      fontWeight: 600,
      backgroundColor: c.bg,
      color: c.color,
      border: `1px solid ${c.border}`,
    };
  },
  rowBg: (status) => {
    if (status === "excluded") return colors.grayBg;
    if (status === "high") return "rgba(35,134,54,0.06)";
    if (status === "medium") return "rgba(158,106,3,0.06)";
    return "rgba(218,54,51,0.06)";
  },
  statsBar: {
    display: "flex",
    gap: "16px",
    padding: "12px 16px",
    backgroundColor: colors.bgCard,
    border: `1px solid ${colors.border}`,
    borderRadius: "8px",
    marginBottom: "16px",
    flexWrap: "wrap",
  },
  statItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "13px",
  },
  statDot: (color) => ({
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: color,
  }),
  filterTab: (active) => ({
    padding: "6px 14px",
    border: `1px solid ${active ? colors.accent : colors.border}`,
    borderRadius: "20px",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: 500,
    backgroundColor: active ? "rgba(88,166,255,0.1)" : "transparent",
    color: active ? colors.accent : colors.textMuted,
  }),
};

// ─── Storage helpers ─────────────────────────────────────────────────────────

function loadStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveStorage(key, val) {
  try {
    window.localStorage.setItem(key, JSON.stringify(val));
  } catch {
    // silently fail
  }
}

// ─── CSV parsing ─────────────────────────────────────────────────────────────

function parseCSVLine(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        current += ch;
      }
    } else {
      if (ch === '"') {
        inQuotes = true;
      } else if (ch === ",") {
        fields.push(current.trim());
        current = "";
      } else {
        current += ch;
      }
    }
  }
  fields.push(current.trim());
  return fields;
}

function detectCSVColumns(headers) {
  const lower = headers.map((h) => h.toLowerCase().replace(/[^a-z0-9]/g, ""));
  let dateIdx = -1, descIdx = -1, amountIdx = -1;
  for (let i = 0; i < lower.length; i++) {
    const h = lower[i];
    if (dateIdx === -1 && (h.includes("date") || h === "posted" || h === "transactiondate")) dateIdx = i;
    if (descIdx === -1 && (h.includes("desc") || h.includes("memo") || h.includes("merchant") || h.includes("payee") || h.includes("narrative") || h.includes("detail") || h.includes("reference"))) descIdx = i;
    if (amountIdx === -1 && (h.includes("amount") || h.includes("charge") || h.includes("debit") || h.includes("total"))) amountIdx = i;
  }
  return { dateIdx, descIdx, amountIdx };
}

function parseAmount(raw) {
  if (!raw) return 0;
  const cleaned = raw.replace(/[$,\s]/g, "").replace(/\((.+)\)/, "-$1");
  const val = parseFloat(cleaned);
  return isNaN(val) ? 0 : val;
}

function parseDate(raw) {
  if (!raw) return "";
  const cleaned = raw.trim().replace(/^["']|["']$/g, "");
  const d = new Date(cleaned);
  if (!isNaN(d.getTime())) {
    return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
  }
  return cleaned;
}

function parseCSVText(text) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return [];
  const headers = parseCSVLine(lines[0]);
  const { dateIdx, descIdx, amountIdx } = detectCSVColumns(headers);
  if (dateIdx === -1 || descIdx === -1 || amountIdx === -1) return [];
  const results = [];
  for (let i = 1; i < lines.length; i++) {
    const fields = parseCSVLine(lines[i]);
    if (fields.length <= Math.max(dateIdx, descIdx, amountIdx)) continue;
    const date = parseDate(fields[dateIdx]);
    const description = fields[descIdx];
    const amount = parseAmount(fields[amountIdx]);
    if (date && description) {
      results.push({ date, description, amount });
    }
  }
  return results;
}

function looksLikeCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return false;
  const first = lines[0].toLowerCase();
  return (first.includes("date") && first.includes(",")) || (lines[0].split(",").length >= 3 && lines[1].split(",").length >= 3);
}

// ─── Auto-coding engine ─────────────────────────────────────────────────────

function autoCodeTransaction(tx, rules) {
  const desc = tx.description.toUpperCase();
  for (const rule of rules) {
    try {
      const regex = new RegExp(rule.pattern, "i");
      if (regex.test(desc)) {
        if (rule.vendor === "__EXCLUDE__" || rule.glCode === "__EXCLUDE__") {
          return { ...tx, vendor: "__EXCLUDE__", glCode: "__EXCLUDE__", glName: "", confidence: "Auto", excluded: true };
        }
        return { ...tx, vendor: rule.vendor, glCode: rule.glCode, glName: rule.glName, confidence: rule.confidence, excluded: false };
      }
    } catch {
      if (desc.includes(rule.pattern.toUpperCase())) {
        if (rule.vendor === "__EXCLUDE__") {
          return { ...tx, vendor: "__EXCLUDE__", glCode: "__EXCLUDE__", glName: "", confidence: "Auto", excluded: true };
        }
        return { ...tx, vendor: rule.vendor, glCode: rule.glCode, glName: rule.glName, confidence: rule.confidence, excluded: false };
      }
    }
  }
  if (tx.amount < 0) {
    return { ...tx, vendor: "__EXCLUDE__", glCode: "__EXCLUDE__", glName: "", confidence: "Auto", excluded: true };
  }
  return { ...tx, vendor: "", glCode: "", glName: "", confidence: "Unmatched", excluded: false };
}

function autoCodeAll(transactions, rules) {
  return transactions.map((tx, i) => ({ ...autoCodeTransaction(tx, rules), id: i }));
}

// ─── Format helpers ──────────────────────────────────────────────────────────

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Math.abs(amount));
}

function formatDateMDY(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.match(/(\d{1,2})\D(\d{1,2})\D(\d{2,4})/);
  if (parts) {
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    let y = parseInt(parts[3], 10);
    if (y < 100) y += 2000;
    return `${m}/${d}/${y}`;
  }
  return dateStr;
}

// ─── Generate AppFolio CSV ───────────────────────────────────────────────────

function generateAppFolioCSV(transactions, settings) {
  const header = "Bill Property Code*,Bill Unit Name,Vendor Payee Name*,Amount*,Bill Account*,Description,Bill Date*,Due Date*,Posting Date*,Bill Reference,Bill Remarks,Memo For Check,Purchase Order Number,Cash Account";
  const rows = transactions
    .filter((tx) => !tx.excluded)
    .map((tx) => {
      const prop = settings.propertyCode;
      const vendor = tx.vendor;
      const amount = Math.abs(tx.amount);
      const gl = tx.glCode;
      const desc = tx.vendor;
      const date = formatDateMDY(tx.date);
      const cash = settings.cashAccount;
      const csvField = (v) => {
        const s = String(v);
        return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
      };
      return [prop, "", csvField(vendor), amount, gl, csvField(desc), date, date, date, csvField(vendor), csvField(vendor), csvField(vendor), "", cash].join(",");
    });
  return [header, ...rows].join("\n");
}

// ─── Components ──────────────────────────────────────────────────────────────

function ImportView({ onImport, rules }) {
  const [dragging, setDragging] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFiles = useCallback(async (files) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const name = file.name.toLowerCase();

    if (name.endsWith(".csv")) {
      setStatus("Parsing CSV...");
      const text = await file.text();
      const txns = parseCSVText(text);
      if (txns.length === 0) {
        setStatus("No transactions found in CSV. Check column headers (Date, Description, Amount).");
        return;
      }
      setStatus(`Found ${txns.length} transactions. Auto-coding...`);
      const coded = autoCodeAll(txns, rules);
      onImport(coded);
    } else if (name.endsWith(".pdf")) {
      setLoading(true);
      setStatus("Reading PDF and sending to Claude API...");
      try {
        const buf = await file.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
        const result = await callClaudeForExtraction(b64, "pdf");
        const coded = autoCodeAll(result, rules);
        setStatus(`Extracted ${result.length} transactions from PDF.`);
        onImport(coded);
      } catch (err) {
        setStatus(`PDF extraction failed: ${err.message}`);
      }
      setLoading(false);
    } else {
      setLoading(true);
      setStatus("Reading file and sending to Claude API...");
      try {
        const text = await file.text();
        if (looksLikeCSV(text)) {
          const txns = parseCSVText(text);
          if (txns.length > 0) {
            const coded = autoCodeAll(txns, rules);
            setStatus(`Found ${txns.length} transactions.`);
            onImport(coded);
            setLoading(false);
            return;
          }
        }
        const result = await callClaudeForTextExtraction(text);
        const coded = autoCodeAll(result, rules);
        setStatus(`Extracted ${result.length} transactions.`);
        onImport(coded);
      } catch (err) {
        setStatus(`Extraction failed: ${err.message}`);
      }
      setLoading(false);
    }
  }, [rules, onImport]);

  const handlePasteSubmit = useCallback(async () => {
    if (!pasteText.trim()) return;
    if (looksLikeCSV(pasteText)) {
      const txns = parseCSVText(pasteText);
      if (txns.length > 0) {
        setStatus(`Parsed ${txns.length} transactions from CSV text.`);
        const coded = autoCodeAll(txns, rules);
        onImport(coded);
        return;
      }
    }
    setLoading(true);
    setStatus("Sending text to Claude API for extraction...");
    try {
      const result = await callClaudeForTextExtraction(pasteText);
      const coded = autoCodeAll(result, rules);
      setStatus(`Extracted ${result.length} transactions.`);
      onImport(coded);
    } catch (err) {
      setStatus(`Extraction failed: ${err.message}`);
    }
    setLoading(false);
  }, [pasteText, rules, onImport]);

  return (
    <div style={s.container}>
      <h2 style={s.h2}>Import Transactions</h2>
      <div style={s.card}>
        <h3 style={s.h3}>Upload File</h3>
        <p style={{ color: colors.textMuted, fontSize: "13px", marginBottom: "16px" }}>
          Drag and drop or click to upload a CSV, PDF, or any text file with transaction data.
        </p>
        <div
          style={s.dropzone(dragging)}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
          onClick={() => fileInputRef.current?.click()}
        >
          <div style={{ fontSize: "32px", marginBottom: "8px", opacity: 0.5 }}>&#128196;</div>
          <div style={{ color: colors.textMuted }}>
            Drop file here or <span style={{ color: colors.accent, textDecoration: "underline" }}>browse</span>
          </div>
          <div style={{ color: colors.textDim, fontSize: "12px", marginTop: "4px" }}>
            CSV, PDF, or any text file
          </div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <div style={s.card}>
        <h3 style={s.h3}>Paste Statement Text</h3>
        <p style={{ color: colors.textMuted, fontSize: "13px", marginBottom: "12px" }}>
          Paste copied text from a bank portal or PDF viewer. CSV text is auto-detected.
        </p>
        <textarea
          style={{ ...s.textarea, minHeight: "160px" }}
          placeholder={"Paste transaction data here...\n\nCSV example:\nDate,Description,Amount\n1/15/2025,MENARDS,32.18\n\nOr paste raw statement text for AI extraction."}
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
        />
        <div style={{ marginTop: "12px" }}>
          <button style={s.btn("primary")} onClick={handlePasteSubmit} disabled={loading || !pasteText.trim()}>
            {loading ? "Processing..." : "Process Text"}
          </button>
        </div>
      </div>

      {status && (
        <div style={{ ...s.card, borderColor: loading ? colors.accent : colors.green }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {loading && <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>&#9696;</span>}
            <span style={{ color: colors.text }}>{status}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewView({ transactions, setTransactions, onExport }) {
  const [filter, setFilter] = useState("all");
  const [expandedRow, setExpandedRow] = useState(null);
  const [editState, setEditState] = useState({});

  const stats = useMemo(() => {
    const total = transactions.length;
    const excluded = transactions.filter((t) => t.excluded).length;
    const high = transactions.filter((t) => !t.excluded && t.confidence === "High").length;
    const medium = transactions.filter((t) => !t.excluded && t.confidence === "Medium").length;
    const unmatched = transactions.filter((t) => !t.excluded && (t.confidence === "Unmatched" || !t.glCode)).length;
    return { total, excluded, high, medium, unmatched, coded: high + medium };
  }, [transactions]);

  const filtered = useMemo(() => {
    if (filter === "review") return transactions.filter((t) => !t.excluded && (t.confidence === "Unmatched" || t.confidence === "Medium" || !t.glCode));
    if (filter === "excluded") return transactions.filter((t) => t.excluded);
    return transactions;
  }, [transactions, filter]);

  const startEdit = (tx) => {
    setExpandedRow(tx.id === expandedRow ? null : tx.id);
    setEditState({ vendor: tx.vendor || "", glCode: tx.glCode || "", glName: tx.glName || "" });
  };

  const saveEdit = (id) => {
    setTransactions((prev) =>
      prev.map((t) =>
        t.id === id
          ? {
              ...t,
              vendor: editState.vendor,
              glCode: editState.glCode,
              glName: editState.glCode ? GL_ACCOUNTS[editState.glCode] || editState.glName : editState.glName,
              confidence: editState.glCode ? "High" : t.confidence,
              excluded: false,
            }
          : t
      )
    );
    setExpandedRow(null);
  };

  const toggleExclude = (id) => {
    setTransactions((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, excluded: !t.excluded, confidence: !t.excluded ? "Auto" : t.confidence } : t
      )
    );
  };

  const saveAsRule = (tx) => {
    if (!editState.vendor || !editState.glCode) return;
    const storedRules = loadStorage("gc_vendor_map", DEFAULT_VENDOR_RULES);
    const keyword = tx.description.slice(0, 20).toUpperCase().trim();
    const newRule = {
      pattern: keyword,
      vendor: editState.vendor,
      glCode: editState.glCode,
      glName: GL_ACCOUNTS[editState.glCode] || "",
      confidence: "High",
    };
    storedRules.push(newRule);
    saveStorage("gc_vendor_map", storedRules);
    saveEdit(tx.id);
  };

  const rowStatus = (tx) => {
    if (tx.excluded) return "excluded";
    if (tx.confidence === "High") return "high";
    if (tx.confidence === "Medium") return "medium";
    return "unmatched";
  };

  return (
    <div style={s.container}>
      <h2 style={s.h2}>Review Transactions</h2>

      <div style={s.statsBar}>
        <div style={s.statItem}>
          <span style={{ fontWeight: 600 }}>{stats.total}</span>
          <span style={{ color: colors.textMuted }}>Total</span>
        </div>
        <div style={s.statItem}>
          <span style={s.statDot(colors.greenText)} />
          <span style={{ fontWeight: 600 }}>{stats.high}</span>
          <span style={{ color: colors.textMuted }}>Auto-coded</span>
        </div>
        <div style={s.statItem}>
          <span style={s.statDot(colors.yellowText)} />
          <span style={{ fontWeight: 600 }}>{stats.medium}</span>
          <span style={{ color: colors.textMuted }}>Medium</span>
        </div>
        <div style={s.statItem}>
          <span style={s.statDot(colors.redText)} />
          <span style={{ fontWeight: 600 }}>{stats.unmatched}</span>
          <span style={{ color: colors.textMuted }}>Unmatched</span>
        </div>
        <div style={s.statItem}>
          <span style={s.statDot(colors.grayText)} />
          <span style={{ fontWeight: 600 }}>{stats.excluded}</span>
          <span style={{ color: colors.textMuted }}>Excluded</span>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        {[
          ["all", `All (${stats.total})`],
          ["review", `Needs Review (${stats.unmatched + stats.medium})`],
          ["excluded", `Excluded (${stats.excluded})`],
        ].map(([key, label]) => (
          <button key={key} style={s.filterTab(filter === key)} onClick={() => setFilter(key)}>
            {label}
          </button>
        ))}
      </div>

      <div style={{ ...s.card, padding: 0, overflow: "auto" }}>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Date</th>
              <th style={s.th}>Vendor</th>
              <th style={s.th}>Description</th>
              <th style={s.th}>GL Account</th>
              <th style={{ ...s.th, textAlign: "right" }}>Amount</th>
              <th style={s.th}>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((tx) => (
              <React.Fragment key={tx.id}>
                <tr
                  style={{ backgroundColor: s.rowBg(rowStatus(tx)), cursor: "pointer", opacity: tx.excluded ? 0.5 : 1 }}
                  onClick={() => startEdit(tx)}
                >
                  <td style={{ ...s.td, ...s.mono, whiteSpace: "nowrap" }}>{tx.date}</td>
                  <td style={s.td}>
                    {tx.excluded ? <span style={{ color: colors.grayText, fontStyle: "italic" }}>Excluded</span> : (tx.vendor || <span style={{ color: colors.redText }}>UNMATCHED</span>)}
                  </td>
                  <td style={{ ...s.td, maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: colors.textMuted }}>
                    {tx.description}
                  </td>
                  <td style={{ ...s.td, ...s.mono, fontSize: "12px" }}>
                    {tx.excluded ? "—" : tx.glCode ? `${tx.glCode}: ${tx.glName}` : <span style={{ color: colors.redText }}>REVIEW</span>}
                  </td>
                  <td style={{ ...s.td, ...s.mono, textAlign: "right", color: tx.amount < 0 ? colors.greenText : colors.text }}>
                    {tx.amount < 0 ? "-" : ""}{formatCurrency(tx.amount)}
                  </td>
                  <td style={s.td}>
                    <span style={s.confidenceBadge(tx.confidence)}>{tx.confidence}</span>
                  </td>
                </tr>
                {expandedRow === tx.id && (
                  <tr style={{ backgroundColor: colors.bgHover }}>
                    <td colSpan={6} style={{ padding: "16px 12px" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                        <div>
                          <label style={s.label}>Vendor Name</label>
                          <input
                            style={s.input}
                            value={editState.vendor}
                            onChange={(e) => setEditState((p) => ({ ...p, vendor: e.target.value }))}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                        <div>
                          <label style={s.label}>GL Account</label>
                          <select
                            style={s.select}
                            value={editState.glCode}
                            onChange={(e) => {
                              const code = e.target.value;
                              setEditState((p) => ({ ...p, glCode: code, glName: GL_ACCOUNTS[code] || "" }));
                            }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <option value="">— Select GL Account —</option>
                            {GL_OPTIONS.map((g) => (
                              <option key={g.code} value={g.code}>{g.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label style={s.label}>Original Description</label>
                          <input style={{ ...s.input, color: colors.textMuted }} value={tx.description} readOnly onClick={(e) => e.stopPropagation()} />
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button style={s.btn("primary")} onClick={(e) => { e.stopPropagation(); saveEdit(tx.id); }}>
                          Save Changes
                        </button>
                        <button style={s.btn("success")} onClick={(e) => { e.stopPropagation(); saveAsRule(tx); }}>
                          Save as Rule
                        </button>
                        <button style={s.btn("ghost")} onClick={(e) => { e.stopPropagation(); toggleExclude(tx.id); }}>
                          {tx.excluded ? "Include" : "Exclude"}
                        </button>
                        <button style={s.btn("ghost")} onClick={(e) => { e.stopPropagation(); setExpandedRow(null); }}>
                          Cancel
                        </button>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ padding: "48px", textAlign: "center", color: colors.textMuted }}>
            No transactions match this filter.
          </div>
        )}
      </div>

      <div style={{ marginTop: "16px", display: "flex", justifyContent: "flex-end" }}>
        <button style={s.btn("success")} onClick={onExport}>
          Proceed to Export &#8594;
        </button>
      </div>
    </div>
  );
}

function ExportView({ transactions, settings }) {
  const [copied, setCopied] = useState(false);

  const nonExcluded = transactions.filter((t) => !t.excluded);
  const uncoded = nonExcluded.filter((t) => !t.glCode);
  const mediumConf = nonExcluded.filter((t) => t.confidence === "Medium");
  const canExport = uncoded.length === 0;

  const glBreakdown = useMemo(() => {
    const map = {};
    nonExcluded.forEach((tx) => {
      if (!tx.glCode) return;
      const key = `${tx.glCode}: ${tx.glName}`;
      if (!map[key]) map[key] = { count: 0, total: 0 };
      map[key].count++;
      map[key].total += Math.abs(tx.amount);
    });
    return Object.entries(map).sort(([, a], [, b]) => b.total - a.total);
  }, [nonExcluded]);

  const csv = useMemo(() => generateAppFolioCSV(transactions, settings), [transactions, settings]);

  const downloadCSV = () => {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `appfolio_upload_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyCSV = async () => {
    try {
      await navigator.clipboard.writeText(csv);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: select textarea
      const el = document.getElementById("csv-preview");
      if (el) { el.select(); document.execCommand("copy"); }
    }
  };

  return (
    <div style={s.container}>
      <h2 style={s.h2}>Export to AppFolio</h2>

      {!canExport && (
        <div style={{ ...s.card, borderColor: colors.red, backgroundColor: colors.redBg }}>
          <div style={{ fontWeight: 600, color: colors.redText, marginBottom: "4px" }}>
            Export Blocked
          </div>
          <div style={{ color: colors.text, fontSize: "13px" }}>
            {uncoded.length} transaction{uncoded.length !== 1 ? "s" : ""} still need GL account assignment.
            Go back to Review to fix them.
          </div>
        </div>
      )}

      {canExport && mediumConf.length > 0 && (
        <div style={{ ...s.card, borderColor: colors.yellow, backgroundColor: colors.yellowBg }}>
          <div style={{ fontWeight: 600, color: colors.yellowText, marginBottom: "4px" }}>
            Warning: Medium Confidence
          </div>
          <div style={{ color: colors.text, fontSize: "13px" }}>
            {mediumConf.length} transaction{mediumConf.length !== 1 ? "s have" : " has"} medium confidence.
            You may want to review before uploading.
          </div>
        </div>
      )}

      <div style={s.card}>
        <h3 style={s.h3}>GL Breakdown Summary</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 100px", gap: "4px 16px" }}>
          <div style={{ ...s.label, marginBottom: "4px" }}>Account</div>
          <div style={{ ...s.label, marginBottom: "4px", textAlign: "right" }}>Count</div>
          <div style={{ ...s.label, marginBottom: "4px", textAlign: "right" }}>Total</div>
          {glBreakdown.map(([key, data]) => (
            <React.Fragment key={key}>
              <div style={{ fontSize: "13px", ...s.mono }}>{key}</div>
              <div style={{ fontSize: "13px", textAlign: "right", ...s.mono }}>{data.count}</div>
              <div style={{ fontSize: "13px", textAlign: "right", ...s.mono }}>{formatCurrency(data.total)}</div>
            </React.Fragment>
          ))}
          <div style={{ gridColumn: "1 / -1", borderTop: `1px solid ${colors.border}`, marginTop: "8px", paddingTop: "8px", display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontWeight: 600 }}>Total ({nonExcluded.length} transactions)</span>
            <span style={{ fontWeight: 600, ...s.mono }}>
              {formatCurrency(nonExcluded.reduce((sum, t) => sum + Math.abs(t.amount), 0))}
            </span>
          </div>
        </div>
      </div>

      <div style={s.card}>
        <h3 style={s.h3}>Download Options</h3>
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          <button style={s.btn(canExport ? "success" : "ghost")} onClick={downloadCSV} disabled={!canExport}>
            Download CSV
          </button>
          <button style={s.btn(canExport ? "primary" : "ghost")} onClick={copyCSV} disabled={!canExport}>
            {copied ? "Copied!" : "Copy to Clipboard"}
          </button>
        </div>
        <label style={s.label}>CSV Preview (click to select all)</label>
        <textarea
          id="csv-preview"
          style={{ ...s.textarea, minHeight: "200px", fontSize: "11px" }}
          value={csv}
          readOnly
          onClick={(e) => e.target.select()}
        />
      </div>
    </div>
  );
}

function SettingsView({ settings, setSettings, rules, setRules }) {
  const [editingRule, setEditingRule] = useState(null);
  const [newRule, setNewRule] = useState({ pattern: "", vendor: "", glCode: "", glName: "", confidence: "High" });

  const handleSettingChange = (key, val) => {
    setSettings((prev) => {
      const next = { ...prev, [key]: val };
      saveStorage("gc_settings", next);
      return next;
    });
  };

  const addRule = () => {
    if (!newRule.pattern || !newRule.vendor || !newRule.glCode) return;
    const updated = [...rules, { ...newRule, glName: GL_ACCOUNTS[newRule.glCode] || newRule.glName }];
    setRules(updated);
    saveStorage("gc_vendor_map", updated);
    setNewRule({ pattern: "", vendor: "", glCode: "", glName: "", confidence: "High" });
  };

  const deleteRule = (idx) => {
    const updated = rules.filter((_, i) => i !== idx);
    setRules(updated);
    saveStorage("gc_vendor_map", updated);
  };

  const updateRule = (idx, field, val) => {
    const updated = rules.map((r, i) => {
      if (i !== idx) return r;
      const next = { ...r, [field]: val };
      if (field === "glCode") next.glName = GL_ACCOUNTS[val] || "";
      return next;
    });
    setRules(updated);
    saveStorage("gc_vendor_map", updated);
  };

  const resetDefaults = () => {
    setRules([...DEFAULT_VENDOR_RULES]);
    saveStorage("gc_vendor_map", DEFAULT_VENDOR_RULES);
    setSettings({ ...DEFAULT_SETTINGS });
    saveStorage("gc_settings", DEFAULT_SETTINGS);
  };

  return (
    <div style={s.container}>
      <h2 style={s.h2}>Settings</h2>

      <div style={s.card}>
        <h3 style={s.h3}>Defaults</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div>
            <label style={s.label}>Default Property Code</label>
            <select style={s.select} value={settings.propertyCode} onChange={(e) => handleSettingChange("propertyCode", e.target.value)}>
              {PROPERTIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label style={s.label}>Default Cash Account</label>
            <select style={s.select} value={settings.cashAccount} onChange={(e) => handleSettingChange("cashAccount", e.target.value)}>
              {CASH_ACCOUNTS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div style={{ marginTop: "16px" }}>
          <button style={s.btn("danger")} onClick={resetDefaults}>
            Reset All to Defaults
          </button>
        </div>
      </div>

      <div style={s.card}>
        <h3 style={s.h3}>Vendor Mapping Rules ({rules.length})</h3>

        <div style={{ marginBottom: "16px", padding: "12px", border: `1px solid ${colors.border}`, borderRadius: "6px", backgroundColor: colors.bg }}>
          <div style={{ ...s.label, marginBottom: "8px" }}>Add New Rule</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 100px auto", gap: "8px", alignItems: "end" }}>
            <div>
              <label style={{ ...s.label, fontSize: "10px" }}>Pattern (regex)</label>
              <input style={s.input} placeholder="e.g. VENDOR|ALT NAME" value={newRule.pattern} onChange={(e) => setNewRule((p) => ({ ...p, pattern: e.target.value }))} />
            </div>
            <div>
              <label style={{ ...s.label, fontSize: "10px" }}>Vendor Name</label>
              <input style={s.input} placeholder="Clean vendor name" value={newRule.vendor} onChange={(e) => setNewRule((p) => ({ ...p, vendor: e.target.value }))} />
            </div>
            <div>
              <label style={{ ...s.label, fontSize: "10px" }}>GL Account</label>
              <select style={s.select} value={newRule.glCode} onChange={(e) => setNewRule((p) => ({ ...p, glCode: e.target.value, glName: GL_ACCOUNTS[e.target.value] || "" }))}>
                <option value="">Select...</option>
                {GL_OPTIONS.map((g) => <option key={g.code} value={g.code}>{g.label}</option>)}
              </select>
            </div>
            <div>
              <label style={{ ...s.label, fontSize: "10px" }}>Confidence</label>
              <select style={s.select} value={newRule.confidence} onChange={(e) => setNewRule((p) => ({ ...p, confidence: e.target.value }))}>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
              </select>
            </div>
            <button style={{ ...s.btn("success"), height: "34px" }} onClick={addRule}>Add</button>
          </div>
        </div>

        <div style={{ overflow: "auto", maxHeight: "500px" }}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Pattern</th>
                <th style={s.th}>Vendor</th>
                <th style={s.th}>GL Account</th>
                <th style={s.th}>Confidence</th>
                <th style={{ ...s.th, width: "60px" }}></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule, idx) => (
                <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
                  <td style={s.td}>
                    {editingRule === idx ? (
                      <input style={{ ...s.input, fontSize: "12px", padding: "4px 8px" }} value={rule.pattern} onChange={(e) => updateRule(idx, "pattern", e.target.value)} />
                    ) : (
                      <code style={{ fontSize: "12px", color: colors.accent }}>{rule.pattern}</code>
                    )}
                  </td>
                  <td style={s.td}>
                    {editingRule === idx ? (
                      <input style={{ ...s.input, fontSize: "12px", padding: "4px 8px" }} value={rule.vendor} onChange={(e) => updateRule(idx, "vendor", e.target.value)} />
                    ) : (
                      <span style={{ fontSize: "13px" }}>{rule.vendor}</span>
                    )}
                  </td>
                  <td style={s.td}>
                    {editingRule === idx ? (
                      <select style={{ ...s.select, fontSize: "12px", padding: "4px 8px" }} value={rule.glCode} onChange={(e) => updateRule(idx, "glCode", e.target.value)}>
                        <option value="">Select...</option>
                        <option value="__EXCLUDE__">__EXCLUDE__</option>
                        {GL_OPTIONS.map((g) => <option key={g.code} value={g.code}>{g.label}</option>)}
                      </select>
                    ) : (
                      <span style={{ ...s.mono, fontSize: "12px" }}>
                        {rule.glCode === "__EXCLUDE__" ? "EXCLUDE" : `${rule.glCode}: ${rule.glName}`}
                      </span>
                    )}
                  </td>
                  <td style={s.td}>
                    <span style={s.confidenceBadge(rule.confidence)}>{rule.confidence}</span>
                  </td>
                  <td style={{ ...s.td, whiteSpace: "nowrap" }}>
                    <button
                      style={{ ...s.btn("ghost"), padding: "2px 8px", fontSize: "11px", marginRight: "4px" }}
                      onClick={() => setEditingRule(editingRule === idx ? null : idx)}
                    >
                      {editingRule === idx ? "Done" : "Edit"}
                    </button>
                    <button
                      style={{ ...s.btn("ghost"), padding: "2px 8px", fontSize: "11px", color: colors.redText }}
                      onClick={() => deleteRule(idx)}
                    >
                      Del
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Claude API integration ──────────────────────────────────────────────────

async function callClaudeForExtraction(base64Data, mediaType) {
  const response = await fetch("/api/claude", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "document",
              source: { type: "base64", media_type: mediaType === "pdf" ? "application/pdf" : "application/octet-stream", data: base64Data },
            },
            {
              type: "text",
              text: 'Extract all transactions from this bank/credit card statement. Return ONLY a JSON array with {date, description, amount} for each transaction. Amount should be positive for charges, negative for credits/payments. Date format: M/D/YYYY. Example: [{"date":"1/15/2025","description":"MENARDS","amount":32.18}]',
            },
          ],
        },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`API error ${response.status}: ${errText}`);
  }

  const data = await response.json();
  const text = data.content?.[0]?.text || "";
  return extractJSONArray(text);
}

async function callClaudeForTextExtraction(text) {
  const response = await fetch("/api/claude", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      messages: [
        {
          role: "user",
          content: `Extract all transactions from this bank/credit card statement text. Return ONLY a JSON array with {date, description, amount} for each transaction. Amount should be positive for charges, negative for credits/payments. Date format: M/D/YYYY. Example: [{"date":"1/15/2025","description":"MENARDS","amount":32.18}]\n\nStatement text:\n${text}`,
        },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`API error ${response.status}: ${errText}`);
  }

  const data = await response.json();
  const responseText = data.content?.[0]?.text || "";
  return extractJSONArray(responseText);
}

function extractJSONArray(text) {
  const jsonMatch = text.match(/\[[\s\S]*\]/);
  if (!jsonMatch) throw new Error("No JSON array found in API response");
  try {
    const arr = JSON.parse(jsonMatch[0]);
    return arr.map((item) => ({
      date: formatDateMDY(item.date || ""),
      description: String(item.description || ""),
      amount: typeof item.amount === "number" ? item.amount : parseAmount(String(item.amount || "0")),
    }));
  } catch (e) {
    throw new Error("Failed to parse JSON from API response");
  }
}

// ─── Main App ────────────────────────────────────────────────────────────────

export default function TransactionReconciler() {
  const [view, setView] = useState("import");
  const [transactions, setTransactions] = useState([]);
  const [rules, setRules] = useState(() => loadStorage("gc_vendor_map", DEFAULT_VENDOR_RULES));
  const [settings, setSettings] = useState(() => loadStorage("gc_settings", DEFAULT_SETTINGS));

  const handleImport = useCallback((coded) => {
    setTransactions(coded);
    setView("review");
  }, []);

  const txCount = transactions.length;
  const needsReview = transactions.filter((t) => !t.excluded && (t.confidence === "Unmatched" || !t.glCode)).length;

  return (
    <div style={s.app}>
      <nav style={s.nav}>
        <div style={s.navBrand}>
          <span style={{ fontSize: "18px" }}>&#9638;</span>
          <span>Transaction Reconciler</span>
          <span style={{ color: colors.textMuted, fontWeight: 400, fontSize: "12px" }}>
            Stone Arch Holdings
          </span>
        </div>
        <div style={s.navTabs}>
          <button style={s.navTab(view === "import")} onClick={() => setView("import")}>
            Import
          </button>
          <button style={s.navTab(view === "review")} onClick={() => setView("review")}>
            Review
            {txCount > 0 && <span style={s.badge}>{txCount}</span>}
          </button>
          <button style={s.navTab(view === "export")} onClick={() => setView("export")}>
            Export
          </button>
          <button style={s.navTab(view === "settings")} onClick={() => setView("settings")}>
            Settings
          </button>
        </div>
        {needsReview > 0 && (
          <div style={{ fontSize: "12px", color: colors.yellowText }}>
            {needsReview} need{needsReview !== 1 ? "" : "s"} review
          </div>
        )}
      </nav>

      {view === "import" && <ImportView onImport={handleImport} rules={rules} />}
      {view === "review" && (
        <ReviewView transactions={transactions} setTransactions={setTransactions} onExport={() => setView("export")} />
      )}
      {view === "export" && <ExportView transactions={transactions} settings={settings} />}
      {view === "settings" && (
        <SettingsView settings={settings} setSettings={setSettings} rules={rules} setRules={setRules} />
      )}
    </div>
  );
}
