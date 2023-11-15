param (
    [string]$token
)

if (-not $token) {
    Write-Host "Por favor, proporciona el token como argumento al script. Ejemplo: -token 'INSERTA_AQUÍ_TU_TOKEN'"
    exit
}

$headers = @{
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $token"
}

$url = "http://localhost:8060/clientes"

$response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers

# Muestra la respuesta del servidor
$response
