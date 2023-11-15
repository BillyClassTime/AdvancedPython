param (
    [string]$usuario,
    [string]$clave=""
)
if (-not $usuario) {
   Write-Host "Por favor, proporciona al menos el usuario. Ejemplo: -usuario 'INSERTA_AQUI_TU_USUARIO'"
   exit
}
$headers = @{
    "Accept"       = "application/json"
    "Content-Type" = "application/json"
}

$body = @{
    username = $usuario
    password = $clave
} | ConvertTo-Json

$url = "http://192.168.88.50:8000/token"

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
    # Muestra la respuesta del servidor
    $response
} catch {
    Write-Host "Error al realizar la solicitud: $_"
}
