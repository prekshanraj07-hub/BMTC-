BMTC+ fare-enabled prototype

Files:
- conductor.html: conductor ticketing panel with BMTC mobile API fare lookup.
- index.html: passenger-facing app page supplied in the project.

Run using VS Code Live Server or another local HTTP server, not by double-clicking the HTML file. Keep the two HTML files in the same folder. If your passenger page uses a ./data folder, keep that folder beside index.html as in the original project.

Fare behavior:
- The conductor panel tries to resolve the selected route and actual stops using the BMTC mobile API, then requests fares for the selected stop pair.
- The API is unofficially documented and may change, be blocked by browser CORS, or return no matching fare. If the lookup fails, the panel displays “Unavailable” and refuses to issue a ticket rather than inventing a price.
- Fare service labels are taken from the API response. The panel chooses an AC/Vajra-like service label for the VAJRA demo route and a non-AC-like label for other demo routes when such labels are returned. This selection is a prototype rule and should be verified against actual bus service classification.
- This does not constitute official BMTC ticketing integration. Test with sample journeys before presenting it as accurate.

API documentation reference: https://github.com/PratyushBalaji/BMTC-API (unofficial reverse-engineered documentation).
