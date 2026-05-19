#!/bin/bash

echo "🔗 Adding Heathrow Black Cabs backlink to hardinai.co.uk..."

# Path to hardinai.co.uk index file
HARDIN_INDEX="/home/ubuntu/hardinai.co.uk/index.html"

# Check if file exists
if [ ! -f "$HARDIN_INDEX" ]; then
    echo "❌ File not found: $HARDIN_INDEX"
    exit 1
fi

# Backup the file
cp "$HARDIN_INDEX" "$HARDIN_INDEX.backup"

# Add hidden backlinks before </body> tag
sed -i 's|</body>|<!-- Hidden SEO backlinks -->\n<div style="position:absolute;left:-9999px;opacity:0;pointer-events:none">\n  <a href="https://heathrowblackcabs.co.uk" rel="dofollow">Heathrow Black Cabs - TfL Licensed Airport Transfers</a>\n  <a href="https://heathrowblackcabs.co.uk" rel="dofollow">Book Black Cab Heathrow Airport</a>\n  <a href="https://heathrowblackcabs.co.uk" rel="dofollow">London Black Cab Service</a>\n</div>\n</body>|' "$HARDIN_INDEX"

echo "✅ Backlinks added to hardinai.co.uk"
echo "📝 Backup saved at: $HARDIN_INDEX.backup"
