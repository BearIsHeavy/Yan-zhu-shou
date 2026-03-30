#!/bin/bash

# =============================================================================
# CHSI Data Fetcher
# =============================================================================
# Usage:
#   ./get_info.sh [page]        - Fetch single page
#   ./get_info.sh all [pages]   - Fetch all pages (default: 10 pages)
#
# Examples:
#   ./get_info.sh 0             - Fetch page 0 -> Info/0.json
#   ./get_info.sh 1             - Fetch page 1 -> Info/1.json
#   ./get_info.sh all           - Fetch pages 0-9 -> Info/0.json to Info/9.json
#   ./get_info.sh all 20        - Fetch pages 0-19 -> Info/0.json to Info/19.json
# =============================================================================

# Output directory
OUTPUT_DIR='Info'
PAGE_SIZE=20

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# =============================================================================
# Raw curl command from browser (Copy from DevTools > Network > Copy as cURL)
# Update this function when cookies expire or you need fresh headers
# Just replace the entire curl command below, keeping the ${start} and ${PAGE_SIZE} variables
# =============================================================================
get_raw_curl() {
    local start=$1
    local output_file=$2
    
    # Paste your curl command here from browser
    # Only need to update:
    # 1. The -b '...' cookie value
    # 2. The --data-raw line (keep ${start} and ${PAGE_SIZE} variables)

    # -- CURL_START --
    curl 'https://yz.chsi.com.cn/sytj/stu/tjyxqexxcx.action' \
      -H 'Accept: application/json, text/plain, */*' \
      -H 'Accept-Language: en-US,en;q=0.9' \
      -H 'Cache-Control: no-cache' \
      -H 'Connection: keep-alive' \
      -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8' \
      -b 'JSESSIONID=YOUR_SESSION_ID; CHSICLTID=YOUR_ID; YOUR_COOKIES_HERE' \
      -H 'Origin: https://yz.chsi.com.cn' \
      -H 'Pragma: no-cache' \
      -H 'Referer: https://yz.chsi.com.cn/sytj/tjyx/qecx.action' \
      -H 'Sec-Fetch-Dest: empty' \
      -H 'Sec-Fetch-Mode: cors' \
      -H 'Sec-Fetch-Site: same-origin' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36' \
      -H 'X-Requested-With: XMLHttpRequest' \
      -H 'sec-ch-ua: "Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"' \
      -H 'sec-ch-ua-mobile: ?0' \
      -H 'sec-ch-ua-platform: "macOS"'
    # -- CURL_END --
      --data-raw "mhcx=1&orderBy=&ssdm2=&mldm2=yjxk&xxfs2=1&zxjh2=0&dwmc2=&fhbktj=1&start=${start}&pageSize=${PAGE_SIZE}" \
      -s -o "${output_file}" -w "%{http_code}"
}

# Function to fetch a single page
fetch_page() {
    local page_num=$1
    local start=$((page_num * PAGE_SIZE))
    local output_file="${OUTPUT_DIR}/${page_num}.json"
    
    # Get HTTP status code from get_raw_curl
    local http_code
    http_code=$(get_raw_curl "${start}" "${output_file}")
    
    # Check HTTP status code
    if [ "${http_code}" = "200" ] && [ -s "${output_file}" ]; then
        echo "✓ Page ${page_num} fetched (start=${start}, HTTP ${http_code}) -> ${output_file}"
        return 0
    else
        echo "✗ Page ${page_num} failed (start=${start}, HTTP ${http_code})"
        rm -f "${output_file}"
        return 1
    fi
}

# Main logic
MODE="${1:-single}"

if [ "${MODE}" = "all" ]; then
    # Fetch all pages
    TOTAL_PAGES="${2:-10}"
    echo "Fetching ${TOTAL_PAGES} pages (0 to $((TOTAL_PAGES - 1)))..."
    echo ""
    
    success_count=0
    fail_count=0
    
    for i in $(seq 0 $((TOTAL_PAGES - 1))); do
        if fetch_page ${i}; then
            ((success_count++))
        else
            ((fail_count++))
            echo ""
            echo "=========================================="
            echo "ABORTED: Request failed at page ${i}"
            echo "=========================================="
            echo ""
            echo "Summary:"
            echo "  - Success: ${success_count}"
            echo "  - Failed:  ${fail_count}"
            echo "=========================================="
            exit 1
        fi
        sleep 3  # Wait 3 seconds between requests to avoid being blocked
    done
    
    echo ""
    echo "=========================================="
    echo "Fetch Complete!"
    echo "  - Success: ${success_count}"
    echo "  - Failed:  ${fail_count}"
    echo "=========================================="
else
    # Fetch single page
    PAGE_NUM="${MODE}"
    fetch_page "${PAGE_NUM}"
fi
