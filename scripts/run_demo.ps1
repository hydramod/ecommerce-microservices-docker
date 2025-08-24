# run_demo.ps1 — verbose demo runner with preflight checks & smarter diagnostics

$ErrorActionPreference = "Stop"

function Show-Step($title) {
  Write-Host ""
  Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Try-ParseJson([string]$s) {
  try {
    if ([string]::IsNullOrWhiteSpace($s)) { return $null }
    return $s | ConvertFrom-Json
  } catch { return $null }
}

function Pretty([object]$obj, [int]$depth = 12) {
  if ($null -eq $obj) { return "<empty>" }
  try {
    return ($obj | ConvertTo-Json -Depth $depth)
  } catch {
    return ($obj | Out-String)
  }
}

function MaskToken([string]$t) {
  if (-not $t) { return "<none>" }
  if ($t.Length -le 12) { return $t }
  return ($t.Substring(0,8) + "..." + $t.Substring($t.Length-6,6))
}

function Call-API {
  param(
    [Parameter(Mandatory=$true)][ValidateSet("GET","POST","PUT","PATCH","DELETE")] [string]$Method,
    [Parameter(Mandatory=$true)][string]$Url,
    [hashtable]$Headers = @{},
    [string]$Body = $null,
    [int[]]$Ok = @(200,201,202,204),   # expected success codes
    [switch]$Quiet
  )

  if (-not $Quiet) {
    Write-Host ""
    Write-Host "-> $Method $Url" -ForegroundColor Yellow
    if ($Headers -and $Headers.Count -gt 0) {
      $printable = @{}
      foreach ($k in $Headers.Keys) {
        $v = $Headers[$k]
        if ($k -match 'Authorization') { $v = "Bearer " + (MaskToken(($v -split ' ')[-1])) }
        $printable[$k] = $v
      }
      Write-Host "   Headers: $(Pretty($printable))"
    } else {
      Write-Host "   Headers: <none>"
    }
    if ($Body) { Write-Host "   Body:    $Body" }
  }

  try {
    $splat = @{
      Method      = $Method
      Uri         = $Url
      Headers     = $Headers
      ErrorAction = 'Stop'
    }
    if ($Body) {
      $splat['ContentType'] = 'application/json'
      $splat['Body']        = $Body
    }

    $resp  = Invoke-WebRequest @splat
    $status = $resp.StatusCode
    $raw    = [string]$resp.Content
    $json   = Try-ParseJson $raw

    if (-not $Quiet) {
      $c = if ($Ok -contains $status) { 'Green' } else { 'Yellow' }
      Write-Host "   Status:  $status" -ForegroundColor $c
      if ($json -ne $null) {
        Write-Host "   JSON:"
        Write-Host (Pretty $json)
      } else {
        if ($raw) {
          Write-Host "   Content:"
          Write-Host $raw
        } else {
          Write-Host "   Content: <empty>"
        }
      }
    }

    return @{
      Status = $status
      Raw    = $raw
      Json   = $json
      Headers= $resp.Headers
    }
  } catch {
    if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errBody = $reader.ReadToEnd()
      $j = Try-ParseJson $errBody
      $code = $null
      try { $code = [int]$_.Exception.Response.StatusCode } catch {}
      if (-not $Quiet) {
        Write-Host "   Status:  $code" -ForegroundColor Red
        if ($j -ne $null) {
          Write-Host "   JSON (error):"
          Write-Host (Pretty $j)
        } elseif ($errBody) {
          Write-Host "   Content (error):"
          Write-Host $errBody
        } else {
          Write-Host "   Error:" -ForegroundColor Red
          Write-Host $_
        }
      }
      return @{
        Status = $code
        Raw    = $errBody
        Json   = $j
        Headers= @{}
        Error  = $_
      }
    } else {
      if (-not $Quiet) {
        Write-Host "   Error:" -ForegroundColor Red
        Write-Host $_
      }
      return @{
        Status = $null
        Raw    = $null
        Json   = $null
        Headers= @{}
        Error  = $_
      }
    }
  }
}

# --- Config / constants ---
$BASE         = "http://localhost"
$AUTH         = "$BASE/auth"
$CATALOG      = "$BASE/catalog/v1"
$CART         = "$BASE/cart/v1"
$ORDER        = "$BASE/order/v1"
$PAYMENT      = "$BASE/payment/v1"

# roots (for health)
$AUTH_ROOT    = "$BASE/auth"
$CATALOG_ROOT = "$BASE/catalog"
$CART_ROOT    = "$BASE/cart"
$ORDER_ROOT   = "$BASE/order"
$PAY_ROOT     = "$BASE/payment"

$ADMIN_EMAIL = "admin@example.com"
$ADMIN_PASS  = "P@ssw0rd!"
$CUST_EMAIL  = "cust@example.com"
$CUST_PASS   = "P@ssw0rd!"

# pull internal key from deploy\.env if present
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$EnvPath  = Join-Path $RepoRoot "deploy\.env"
$INTERNAL = $null
if (Test-Path $EnvPath) {
  $line = Select-String -Path $EnvPath -Pattern '^\s*SVC_INTERNAL_KEY\s*=' | Select-Object -First 1
  if ($line) {
    $raw = $line.Line.Split('=',2)[1].Trim()
    if ($raw.StartsWith('"') -and $raw.EndsWith('"')) { $raw = $raw.Substring(1, $raw.Length-2) }
    if ($raw.StartsWith("'") -and $raw.EndsWith("'")) { $raw = $raw.Substring(1, $raw.Length-2) }
    $INTERNAL = $raw
  }
}
if (-not $INTERNAL) { $INTERNAL = "devkey" }

# --- Preflight: health checks ---
Show-Step "Preflight: service health"
$checks = @(
  @{ name="auth";    url="$AUTH_ROOT/health"    },
  @{ name="catalog"; url="$CATALOG_ROOT/health" },
  @{ name="cart";    url="$CART_ROOT/health"    },
  @{ name="order";   url="$ORDER_ROOT/health"   },
  @{ name="payment"; url="$PAY_ROOT/health"     }
)
foreach ($c in $checks) {
  $r = Call-API -Method GET -Url $c.url -Ok 200 -Quiet
  $status = if ($r.Status -eq 200) { "OK" } else { "FAIL ($($r.Status))" }
  Write-Host ("  - {0,-8} -> {1}" -f $c.name, $status) -ForegroundColor ($(if ($r.Status -eq 200) { "Green" } else { "Red" }))
}

# --- 1) Admin register + login ---
Show-Step "Admin: register"
$null = Call-API -Method POST -Url "$AUTH/register" -Ok 201 -Body (@{
  email = $ADMIN_EMAIL
  password = $ADMIN_PASS
  role = "admin"
} | ConvertTo-Json)

Show-Step "Admin: login"
$adminLogin = Call-API -Method POST -Url "$AUTH/login" -Ok 200 -Body (@{
  email = $ADMIN_EMAIL
  password = $ADMIN_PASS
} | ConvertTo-Json)

$AACCESS = $null
if ($adminLogin.Json) { $AACCESS = $adminLogin.Json.access_token }
Write-Host ("Admin access token: " + (MaskToken $AACCESS))

# --- 2) Admin create category + product ---
Show-Step "Admin: create category"
$catResp = Call-API -Method POST -Url "$CATALOG/categories" `
  -Headers @{ Authorization = "Bearer $AACCESS" } `
  -Ok 201,409 `
  -Body (@{ name = "Shoes" } | ConvertTo-Json)

Show-Step "Admin: create product"
$prodResp = Call-API -Method POST -Url "$CATALOG/products" `
  -Headers @{ Authorization = "Bearer $AACCESS" } `
  -Ok 201,409 `
  -Body (@{
    title = "Air Zoom"
    description = "Runner"
    price_cents = 12999
    currency = "USD"
    sku = "SKU-001"
    category_id = 1
    active = $true
  } | ConvertTo-Json)

# Quick sanity: product should be reachable via gateway
Show-Step "Sanity: fetch product #1 (gateway)"
$prodGet = Call-API -Method GET -Url "$CATALOG/products/1" -Ok 200,404

# --- 3) Admin restock inventory (prefer Internal Key; also send admin JWT) ---
Show-Step "Admin: restock inventory (X-Internal-Key + Authorization)"
$restockResp = Call-API -Method POST -Url "$CATALOG/inventory/restock" `
  -Headers @{
    "X-Internal-Key" = $INTERNAL
    "Authorization"  = "Bearer $AACCESS"
  } `
  -Ok 200 `
  -Body (@{
    items = @(@{ product_id = 1; qty = 50 })
  } | ConvertTo-Json)

# --- 4) Customer register + login ---
Show-Step "Customer: register"
$null = Call-API -Method POST -Url "$AUTH/register" -Ok 201,409 -Body (@{
  email = $CUST_EMAIL
  password = $CUST_PASS
} | ConvertTo-Json)

Show-Step "Customer: login"
$custLogin = Call-API -Method POST -Url "$AUTH/login" -Ok 200 -Body (@{
  email = $CUST_EMAIL
  password = $CUST_PASS
} | ConvertTo-Json)

$CACCESS = $null
if ($custLogin.Json) { $CACCESS = $custLogin.Json.access_token }
Write-Host ("Customer access token: " + (MaskToken $CACCESS))

# --- 5) Customer add to cart ---
Show-Step "Customer: add to cart"
$addCart = Call-API -Method POST -Url "$CART/cart/items" `
  -Headers @{ Authorization = "Bearer $CACCESS" } `
  -Ok 200,201 `
  -Body (@{ product_id = 1; qty = 2 } | ConvertTo-Json)

# If 404, print helpful hint about CATALOG_BASE inside the cart container
if ($addCart.Status -eq 404) {
  Write-Host ""
  Write-Host "Hint: Cart returned 404. This often means the cart service can't reach catalog." -ForegroundColor Yellow
  Write-Host "      Ensure the cart container has CATALOG_BASE set, e.g. CATALOG_BASE=http://catalog:8000" -ForegroundColor Yellow
  Write-Host "      You can verify inside the container:" -ForegroundColor Yellow
  Write-Host "        docker compose -f deploy\docker-compose.yaml --env-file deploy\.env exec cart sh -lc `"env | grep CATALOG_BASE`"" -ForegroundColor Yellow
  Write-Host "        docker compose -f deploy\docker-compose.yaml --env-file deploy\.env exec cart sh -lc `"apk add --no-cache curl >/dev/null 2>&1 || true; curl -i \$CATALOG_BASE/v1/products/1`"" -ForegroundColor Yellow
}

# --- 6) Checkout ---
Show-Step "Customer: checkout"
$checkout = Call-API -Method POST -Url "$ORDER/orders/checkout" `
  -Headers @{ Authorization = "Bearer $CACCESS" } `
  -Ok 200

$ORDER_ID = $null
$AMOUNT   = $null
if ($checkout.Json) {
  $ORDER_ID = $checkout.Json.order_id
  $AMOUNT   = $checkout.Json.total_cents
}
Write-Host "Order ID: $ORDER_ID; Amount: $AMOUNT"

# --- 7) Payment: mock succeed ---
Show-Step "Payment: mock succeed"
$pay = Call-API -Method POST -Url "$PAYMENT/payments/mock-succeed" `
  -Ok 200 `
  -Body (@{
    order_id = $ORDER_ID
    amount_cents = $AMOUNT
    currency = "USD"
  } | ConvertTo-Json)

Start-Sleep -Seconds 2

# --- 8) Check order status ---
Show-Step "Order: check status"
$final = Call-API -Method GET -Url "$ORDER/orders/$ORDER_ID" -Ok 200,404

Write-Host ""
Write-Host "=== DEMO COMPLETE ===" -ForegroundColor Green
