#!/bin/sh
set -e

###
# This script is used in the GitHub Actions workflows "Deploy" and "Release"
###

# get the total coverage percentage and round it to 2 decimals
total=$(jq ".totals.percent_covered" public/coverage.json)
total=$(echo "${total}" | awk '{ printf("%3.2f\n", $1) }')
inttotal=$(echo "${total}" | cut -d "." -f1)

if [ "${inttotal}" -ge "90"  ]; then
  COLOR="#008000"  # green
elif [ "${inttotal}" -ge "80" ]; then
  COLOR="#ffa500"  # orange
else
  COLOR="#ff0000"  # red
fi

echo "<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"116\" height=\"20\" role=\"img\" aria-label=\"Coverage: ${total}%\"><title>Coverage: ${total}%</title><linearGradient id=\"s\" x2=\"0\" y2=\"100%\"><stop offset=\"0\" stop-color=\"#bbb\" stop-opacity=\".1\"/><stop offset=\"1\" stop-opacity=\".1\"/></linearGradient><clipPath id=\"r\"><rect width=\"116\" height=\"20\" rx=\"3\" fill=\"#fff\"/></clipPath><g clip-path=\"url(#r)\"><rect width=\"63\" height=\"20\" fill=\"#555\"/><rect x=\"63\" width=\"53\" height=\"20\" fill=\"${COLOR}\"/><rect width=\"116\" height=\"20\" fill=\"url(#s)\"/></g><g fill=\"#fff\" text-anchor=\"middle\" font-family=\"Verdana,Geneva,DejaVu Sans,sans-serif\" text-rendering=\"geometricPrecision\" font-size=\"110\"><text aria-hidden=\"true\" x=\"325\" y=\"150\" fill=\"#010101\" fill-opacity=\".3\" transform=\"scale(.1)\" textLength=\"530\">Coverage</text><text x=\"325\" y=\"140\" transform=\"scale(.1)\" fill=\"#fff\" textLength=\"530\">Coverage</text><text aria-hidden=\"true\" x=\"885\" y=\"150\" fill=\"#010101\" fill-opacity=\".3\" transform=\"scale(.1)\" textLength=\"430\">${total}%</text><text x=\"885\" y=\"140\" transform=\"scale(.1)\" fill=\"#fff\" textLength=\"430\">${total}%</text></g></svg>"
