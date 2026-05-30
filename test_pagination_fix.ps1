# Test Pagination and Total Count Fix
Write-Host "=== Testing Pagination and Total Count Fix ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000/api/v1"

# Test 1: Check if total count is in millions
Write-Host "[Test 1] Checking Total Count (should be millions)" -ForegroundColor Yellow
$body = @{
    query = "machine learning"
    filters = @{
        year_from = $null
        year_to = $null
        sources = @("arxiv", "core", "crossref", "doaj", "europepmc", "openalex", "pubmed", "semantic_scholar")
        open_access = $null
        min_citations = $null
        venue_contains = $null
        topic = $null
        institution = $null
        type = $null
    }
    limit = 25
    offset = 0
    sort_by = "relevance"
} | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-RestMethod -Uri "$baseUrl/search" -Method Post -Body $body -ContentType "application/json"
    $total1 = $response1.total
    $results1Count = $response1.results.Count
    
    Write-Host "  Total: $total1" -ForegroundColor $(if ($total1 -gt 1000000) { "Green" } else { "Red" })
    Write-Host "  Results Count: $results1Count" -ForegroundColor $(if ($results1Count -eq 25) { "Green" } else { "Red" })
    
    if ($total1 -gt 1000000) {
        Write-Host "  ✅ PASS: Total is in millions ($total1)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Total should be millions, got $total1" -ForegroundColor Red
    }
    
    # Save first paper title for consistency check
    $firstPaperTitle = $response1.results[0].title
    Write-Host "  First paper: $firstPaperTitle" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ FAIL: Request failed - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Check pagination (page 2 should be different)
Write-Host "[Test 2] Checking Pagination Consistency" -ForegroundColor Yellow
$body2 = @{
    query = "machine learning"
    filters = @{
        year_from = $null
        year_to = $null
        sources = @("arxiv", "core", "crossref", "doaj", "europepmc", "openalex", "pubmed", "semantic_scholar")
        open_access = $null
        min_citations = $null
        venue_contains = $null
        topic = $null
        institution = $null
        type = $null
    }
    limit = 25
    offset = 25
    sort_by = "relevance"
} | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-RestMethod -Uri "$baseUrl/search" -Method Post -Body $body2 -ContentType "application/json"
    $total2 = $response2.total
    $results2Count = $response2.results.Count
    $secondPageFirstTitle = $response2.results[0].title
    
    Write-Host "  Page 2 Total: $total2" -ForegroundColor $(if ($total2 -eq $total1) { "Green" } else { "Red" })
    Write-Host "  Page 2 Results Count: $results2Count" -ForegroundColor $(if ($results2Count -gt 0) { "Green" } else { "Red" })
    Write-Host "  Page 2 First paper: $secondPageFirstTitle" -ForegroundColor Gray
    
    if ($total2 -eq $total1) {
        Write-Host "  ✅ PASS: Total is consistent across pages" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Total changed from $total1 to $total2" -ForegroundColor Red
    }
    
    if ($secondPageFirstTitle -ne $firstPaperTitle) {
        Write-Host "  ✅ PASS: Page 2 has different papers (no duplicates)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Page 2 has same first paper as page 1" -ForegroundColor Red
    }
    
    if ($results2Count -gt 0) {
        Write-Host "  ✅ PASS: Page 2 has results" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Page 2 has no results" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAIL: Request failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Check cache performance (page 3 should be fast)
Write-Host "[Test 3] Checking Cache Performance" -ForegroundColor Yellow
$body3 = @{
    query = "machine learning"
    filters = @{
        year_from = $null
        year_to = $null
        sources = @("arxiv", "core", "crossref", "doaj", "europepmc", "openalex", "pubmed", "semantic_scholar")
        open_access = $null
        min_citations = $null
        venue_contains = $null
        topic = $null
        institution = $null
        type = $null
    }
    limit = 25
    offset = 50
    sort_by = "relevance"
} | ConvertTo-Json -Depth 10

try {
    $startTime = Get-Date
    $response3 = Invoke-RestMethod -Uri "$baseUrl/search" -Method Post -Body $body3 -ContentType "application/json"
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalMilliseconds
    
    Write-Host "  Page 3 Response Time: $([math]::Round($duration, 0))ms" -ForegroundColor $(if ($duration -lt 500) { "Green" } else { "Yellow" })
    Write-Host "  Page 3 Results Count: $($response3.results.Count)" -ForegroundColor $(if ($response3.results.Count -gt 0) { "Green" } else { "Red" })
    
    if ($duration -lt 500) {
        Write-Host "  ✅ PASS: Cache is working (fast response)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  WARNING: Response slower than expected (may not be cached)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ FAIL: Request failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "If all tests pass:" -ForegroundColor White
Write-Host "  ✅ Total count shows millions of papers" -ForegroundColor Green
Write-Host "  ✅ Pagination works consistently" -ForegroundColor Green
Write-Host "  ✅ Cache improves performance" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Test in browser at http://localhost:5173" -ForegroundColor Yellow
