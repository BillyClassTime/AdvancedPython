param(
    [string]$projectPath = ".\",
    [string]$pythonVersion = "3.9"
)

# Define la ruta principal del proyecto
$proyectoPath = $projectPath

# Función para crear directorio si no existe
function CrearDirectorio($ruta) {
    if (-not (Test-Path $ruta)) {
        New-Item -Path $ruta -ItemType Directory -ErrorAction SilentlyContinue
    } else {
        return "El directorio '$ruta' ya existe. No se creará uno nuevo."
    }
    return $ruta
}

# Función para crear archivo si no existe
function CrearArchivo($ruta) {
    if (-not (Test-Path $ruta)) {
        New-Item -Path $ruta -ItemType File -ErrorAction SilentlyContinue
    } else {
        return "El archivo '$ruta' ya existe. No se creará uno nuevo."
    }
    return $ruta
}

# Crea la estructura de carpetas y archivos
$log = "Estructura de proyecto`nFicheros y directorios creados:`n" -f ""
try {
    $log+="$(CrearDirectorio $proyectoPath)`n"

    $apiPath = Join-Path $proyectoPath "api"
    $log+="$(CrearDirectorio $apiPath)`n"

    $routesPath = Join-Path $apiPath "routes"
    $log+="$(CrearDirectorio $routesPath)`n"

    $routesFiles = @("__init__.py", "manageRoutes.py")
    foreach ($file in $routesFiles) {
        $log+="$(CrearArchivo (Join-Path $routesPath $file))`n"
    }

    $appCorePath = Join-Path $proyectoPath "app_core"
    $log+="$(CrearDirectorio $appCorePath)`n"

    $appCoreFiles = @("__init__.py", "initializer.py")
    foreach ($file in $appCoreFiles) {
        $log+="$(CrearArchivo (Join-Path $appCorePath $file))`n"
    }

    $servicesPath = Join-Path $proyectoPath "services"
    $log+="$(CrearDirectorio $servicesPath)`n"

    $servicesFiles = @("__init__.py", "manageServices.py")
    foreach ($file in $servicesFiles) {
        $log+="$(CrearArchivo (Join-Path $servicesPath $file))`n"
    }

    $log+="$(CrearArchivo (Join-Path $proyectoPath "requeriment.txt"))`n"

    $testPath = Join-Path $proyectoPath "test"
    $log+="$(CrearDirectorio $testPath)`n"

    $testFiles = @("__init__.py", "unit_integration.py")
    foreach ($file in $testFiles) {
        $log+="$(CrearArchivo (Join-Path $testPath $file))`n"
    }

    $log+="$(CrearArchivo (Join-Path $proyectoPath "main.py"))`n"

} catch {
    $log+="Error al crear la estructura de carpetas y archivos: $_"
}

cls
Write-Host $log

# Carpeta env
$envPath = Join-Path $proyectoPath "env"

# Verifica si el directorio ya existe
if (-not (Test-Path $envPath)) {
    # Crea el entorno virtual de Python
    try {
        Write-Host "Creando entorno virtual python version $pythonVersion"
        py -$pythonVersion -m venv $envPath
        Write-Host "Entorno virtual de Python creado exitosamente."
    } catch {
        Write-Host "Error al crear el entorno virtual de Python: $_"
    }
} else {
    Write-Host "El directorio 'env' ya existe. No se creará un nuevo entorno virtual."
}

# Activa el entorno virtual
$activateScript = Join-Path $envPath "Scripts\Activate"
if (Test-Path $activateScript) {
    try {
        . $activateScript
        Write-Host "Entorno virtual de Python activado."
    } catch {
        Write-Host "Error al activar el entorno virtual de Python: $_"
    }
} else {
    Write-Host "No se pudo encontrar el script de activación del entorno virtual."
}

# Actualiza pip
try {
    py -m pip install --upgrade pip
    Write-Host "pip actualizado exitosamente."
} catch {
    Write-Host "Error al actualizar pip: $_"
}
