BMTC+ fixed frontend files

Files:
- conductor.html: conductor ticket panel; stores tickets under buses/{routeId}/passengers and updates buses/{routeId}/occupancy.
- index.html: passenger companion; reads the same buses/{routeId} data and shows shared occupancy.

Changes made:
1. Restored escaped HTML/URL punctuation so Firebase/Leaflet CDN script URLs are valid.
2. Removed the misleading diagnosis that labelled every non-200 REST probe as a missing database.
3. Fixed the passenger stop-name normalization regex.
4. Added the missing Papa Parse script required by the GTFS CSV loader.

Firebase config in both pages matches the project details provided in your pasted source and console: https://bmtc-plus-default-rtdb.firebaseio.com

IMPORTANT:
- Keep the pages together with your existing data/ folder and service worker/assets from your original project. This ZIP cannot include those files because they were not among the two files provided.
- The source uses open test-mode database rules. Do not use real passenger/ticket data until authentication and restrictive database rules are configured.
- These are frontend files using Firebase's client SDK, not a separate trusted server backend. A real production ticketing system should validate ticket/fare operations server-side.

Test: open the pages through a local web server (not file://) or your existing hosting deployment. In VS Code, Live Server can serve the folder. Then issue a test ticket in conductor.html and check whether index.html updates the corresponding bus crowd.
