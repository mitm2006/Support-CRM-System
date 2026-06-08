$base = 'http://127.0.0.1:8000'
$pass = 0
$fail = 0

function Check($label, $condition) {
    if ($condition) {
        Write-Host "  [PASS] $label" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  [FAIL] $label" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n=== Datastraw CRM Smoke Tests ===`n"

# 1. Create ticket
Write-Host "1. POST /api/tickets"
$b = @{ customer_name="Rahul Sharma"; customer_email="rahul@example.com"; subject="Order not received"; description="Order 1234 missing" } | ConvertTo-Json
$c = Invoke-RestMethod -Uri "$base/api/tickets" -Method POST -Body $b -ContentType "application/json"
Check "Returns ticket_id" ($c.ticket_id -like "TKT-*")
Check "Returns id" ($null -ne $c.id)
Check "Returns created_at" ($null -ne $c.created_at)
$tid = $c.id
Write-Host "  -> Created $($c.ticket_id) (id=$tid)"

# 2. Create second ticket
Write-Host "`n2. POST /api/tickets (second)"
$b2 = @{ customer_name="Priya Mehta"; customer_email="priya@example.com"; subject="Billing issue" } | ConvertTo-Json
$c2 = Invoke-RestMethod -Uri "$base/api/tickets" -Method POST -Body $b2 -ContentType "application/json"
Check "Second ticket has incremented id" ($c2.id -gt $tid)
Write-Host "  -> Created $($c2.ticket_id)"

# 3. List all
Write-Host "`n3. GET /api/tickets"
$list = Invoke-RestMethod -Uri "$base/api/tickets"
Check "Returns array" ($list -is [array])
Check "At least 2 tickets" ($list.Count -ge 2)
Check "Each item has ticket_id" (($list | Where-Object { $_.ticket_id -like "TKT-*" }).Count -eq $list.Count)

# 4. Search by name
Write-Host "`n4. GET /api/tickets?search=Rahul"
$srch = Invoke-RestMethod -Uri "$base/api/tickets?search=Rahul"
Check "Returns results" ($srch.Count -ge 1)
Check "Match contains Rahul" (($srch | Where-Object { $_.customer_name -like "*Rahul*" }).Count -ge 1)

# 5. Search by TKT ID
Write-Host "`n5. GET /api/tickets?search=TKT-$('{0:d3}' -f $tid)"
$tktSearch = "TKT-$('{0:d3}' -f $tid)"
$srch2 = Invoke-RestMethod -Uri "$base/api/tickets?search=$tktSearch"
Check "TKT-NNN search returns result" ($srch2.Count -ge 1)

# 6. Filter Open
Write-Host "`n6. GET /api/tickets?status=Open"
$open = Invoke-RestMethod -Uri "$base/api/tickets?status=Open"
Check "All results are Open" (($open | Where-Object { $_.status -ne "Open" }).Count -eq 0)

# 7. Ticket detail
Write-Host "`n7. GET /api/tickets/$tid"
$detail = Invoke-RestMethod -Uri "$base/api/tickets/$tid"
Check "ticket_id matches" ($detail.ticket_id -eq "TKT-$('{0:d3}' -f $tid)")
Check "customer_name correct" ($detail.customer_name -eq "Rahul Sharma")
Check "notes is array" ($detail.notes -is [array])
Check "description present" ($null -ne $detail.description)

# 8. Update status + note
Write-Host "`n8. PUT /api/tickets/$tid"
$upd = @{ status="In Progress"; note_text="Escalated to warehouse team." } | ConvertTo-Json
$updR = Invoke-RestMethod -Uri "$base/api/tickets/$tid" -Method PUT -Body $upd -ContentType "application/json"
Check "success=true" ($updR.success -eq $true)
Check "has updated_at" ($null -ne $updR.updated_at)

# 9. Verify update persisted
Write-Host "`n9. Verify status + note saved"
$detail2 = Invoke-RestMethod -Uri "$base/api/tickets/$tid"
Check "Status changed to In Progress" ($detail2.status -eq "In Progress")
Check "Note was saved" ($detail2.notes.Count -eq 1)
Check "Note text correct" ($detail2.notes[0].note_text -eq "Escalated to warehouse team.")

# 10. Filter In Progress
Write-Host "`n10. GET /api/tickets?status=In Progress"
$inprog = @(Invoke-RestMethod -Uri "$base/api/tickets?status=In+Progress")
Check "Updated ticket in In Progress filter" (($inprog | Where-Object { $_.id -eq $tid }).Count -ge 1)

# 11. Page routes
Write-Host "`n11. HTML page routes"
try { $hStat = (Invoke-WebRequest -Uri "$base/" -MaximumRedirection 5 -UseBasicParsing).StatusCode } catch { $hStat = 0 }
try { $cStat = (Invoke-WebRequest -Uri "$base/create" -MaximumRedirection 5 -UseBasicParsing).StatusCode } catch { $cStat = 0 }
try { $dStat = (Invoke-WebRequest -Uri "$base/detail" -MaximumRedirection 5 -UseBasicParsing).StatusCode } catch { $dStat = 0 }
Check "GET / returns 200"       ($hStat -eq 200)
Check "GET /create returns 200" ($cStat -eq 200)
Check "GET /detail returns 200" ($dStat -eq 200)

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($fail -eq 0) {
    Write-Host "ALL $pass TESTS PASSED" -ForegroundColor Green
} else {
    Write-Host "$pass passed, $fail FAILED" -ForegroundColor Red
    exit 1
}
