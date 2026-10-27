[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) देखें। संक्षेप में:

| भाग | कहाँ |
|---|---|
| Vault: फ़ोल्डर, तथ्य, छिपे हुए टैग वाले सेक्शन | `mnema/vault.py`, `mnema/memory.py` |
| प्रत्येक AI के लिए एक्सेस नियम | `mnema/clients.py` |
| जर्नल और अनडू | `mnema/journal.py` |
| MCP सर्वर, कमांड लाइन | `mnema/mcp_server.py`, `mnema/cli.py` |
| लोकल API और विंडो | `mnema/api*.py`, `mnema/desktop.py` |
| इंटरफ़ेस | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (क्रम से लोड होते हैं) |
| किसी भी मॉडल के साथ चैट, कंसोर्शियम, फ़ाइलों के साथ कार्य | `mnema/chat/` |
| सीखना: स्रोत, ब्रेन, निर्णय | `mnema/learn/` |
| कंप्यूटर से बाहर क्या जाता है | `mnema/outgoing.py` |
| Windows, macOS और Linux में क्या अलग है | `mnema/osapi.py` |
| पासवर्ड द्वारा मेमोरी का एन्क्रिप्शन | `mnema/crypt.py` |
| स्कैन और चित्रों से टेक्स्ट | `mnema/ocr.py` |
| नॉलेज बेस जिससे असिस्टेंट उत्तर देता है | `mnema/knowledge/mnema.md` |
