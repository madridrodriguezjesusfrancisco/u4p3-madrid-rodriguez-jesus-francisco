# =====================================================
# verificar_entrega.py — kit de entrega de la práctica u4p3
# Revisa tu repositorio ANTES de entregar, con las mismas reglas que usa el profesor:
#   • el nombre del repo (u4p3-paterno-materno-nombres) y tu firma en los commits
#   • los archivos nuevos, las migraciones y las 6 consultas SQL
#   • que el .env NO esté en el repositorio
#   • los 13 commits ("paso 02" … "paso 12", "paso 15" y "evidencias")
#   • EVIDENCIAS.md (minutos llenos y capturas que existen)
#   • que todo esté subido a GitHub (sin cambios ni commits pendientes)
# Uso (terminal de VS Code, en la carpeta que tiene manage.py, con (venv) activo):
#   python verificar_entrega.py
# No cambia nada de tu proyecto: solo lee y te dice qué falta.
# =====================================================

# re: expresiones regulares para buscar patrones en nombres, commits y código
import re
# subprocess: para correr comandos de git desde Python
import subprocess
# sys: para cambiar la salida de la terminal a UTF-8 (acentos y ✅)
import sys
# Path: para armar rutas de archivos que funcionan en Windows
from pathlib import Path

# la terminal de Windows a veces no muestra acentos ni emojis; esto lo arregla
sys.stdout.reconfigure(encoding="utf-8")

# CARPETA: la carpeta donde está este archivo (la misma que tiene manage.py)
CARPETA = Path(__file__).resolve().parent
# NOMBRE_REPO: u4p3- + apellidos y nombres en minúsculas, sin acentos, separados por guiones
NOMBRE_REPO = re.compile(r"^u4p3-[a-z]+-[a-z]+-[a-z]+(?:-[a-z]+)*$")
# PASOS_CON_COMMIT: pasos que cambian archivos y llevan su commit "paso NN"
PASOS_CON_COMMIT = list(range(2, 13)) + [15]
# ARCHIVOS: archivos que deben existir al terminar la práctica
ARCHIVOS = [
    # las 6 consultas SQL escritas a mano (paso 08)
    "core/reportes.py",
    # el comando de datos de prueba (paso 12)
    "core/management/commands/cargar_demo.py",
    # la lista de reportes (paso 11)
    "core/templates/core/reportes.html",
    # la tabla genérica de un reporte (paso 11)
    "core/templates/core/reporte.html",
    # el formulario de factura con renglones (paso 11)
    "core/templates/core/factura_form.html",
    # el archivo con los minutos del video (paso 16)
    "EVIDENCIAS.md",
]
# MINUTO: hh:mm:ss o mm:ss dentro de una fila de EVIDENCIAS.md
MINUTO = re.compile(r"\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b")
# ICONOS: cómo se pinta cada estado en la terminal
ICONOS = {"ok": "✅", "revisar": "⚠️ ", "falla": "❌"}


def git(*args):
    """Corre un comando de git en esta carpeta y devuelve lo que imprime ("" si falla)."""
    # run: ejecuta git, captura la salida y no truena si hay error
    r = subprocess.run(["git", *args], cwd=CARPETA, capture_output=True, text=True, encoding="utf-8", errors="replace")
    # devuelve la salida sin espacios al final
    return r.stdout.strip()


def leer(ruta):
    """Devuelve el texto de un archivo del proyecto, o "" si no existe."""
    # arma la ruta completa dentro del proyecto
    archivo = CARPETA / ruta
    # si existe lo lee; si no, regresa texto vacío
    return archivo.read_text("utf-8", "replace") if archivo.exists() else ""


def revisar_nombre():
    """Nombre del repo según el remote origin; regresa (punto, firma)."""
    # URL del repositorio al que apunta origin
    url = git("remote", "get-url", "origin")
    # sin origin todavía no hay repositorio en GitHub
    if not url:
        # se avisa y no hay firma que comparar
        return ("revisar", "todavía no tienes remote origin (se configura en el paso 15)"), ""
    # última parte de la URL, sin .git: el nombre del repositorio
    nombre = url.rstrip("/").split("/")[-1].removesuffix(".git")
    # si no empieza con u4p3- seguramente sigue apuntando al repo de la semana anterior
    if not nombre.startswith("u4p3-"):
        # se avisa: en el paso 15 se cambia con git remote set-url
        return ("revisar", f"origin apunta a '{nombre}'; en el paso 15 cámbialo a tu repo u4p3-…"), ""
    # compara contra la regla de nombre
    if not NOMBRE_REPO.match(nombre):
        # mayúsculas, acentos, ñ o espacios en el nombre
        return ("falla", f"'{nombre}' no sigue u4p3-paterno-materno-nombres (minúsculas, sin acentos, ñ→n)"), ""
    # la firma de los commits es el nombre sin "u4p3-"
    return ("ok", nombre), nombre.removeprefix("u4p3-")


def revisar_archivos():
    """Los archivos nuevos de la práctica existen."""
    # lista de los que no están
    faltan = [a for a in ARCHIVOS if not (CARPETA / a).exists()]
    # ok si no falta ninguno
    return ("ok", "completos") if not faltan else ("falla", "faltan: " + ", ".join(faltan))


def revisar_migraciones():
    """Las migraciones de los pasos 02 a 05 tienen sus operaciones."""
    # junta el texto de todas las migraciones de la app core
    texto = "\n".join(p.read_text("utf-8", "replace") for p in (CARPETA / "core" / "migrations").glob("*.py"))
    # operación que debe aparecer → para qué sirve
    necesarias = {"RunPython": "migración de datos (paso 03)", "RemoveField": "quitar texto (paso 04)",
                  # renombrar la llave foránea y los índices de las facturas
                  "RenameField": "renombrar FK (paso 04)", "models.Index": "índices (paso 05)"}
    # las que no aparecen en ningún archivo
    sin = [desc for clave, desc in necesarias.items() if clave not in texto]
    # ok si están todas
    return ("ok", "datos, quitar, renombrar e índices") if not sin else ("falla", "falta: " + ", ".join(sin))


def revisar_sql():
    """reportes.py: 6 consultas, filtro %(uid)s y nada de SQL armado con f-strings."""
    # texto de core/reportes.py
    rep = leer("core/reportes.py")
    # sin archivo no hay consultas
    if not rep:
        # falla
        return "falla", "no existe core/reportes.py"
    # cuántos reportes tienen su "clave"
    claves = len(re.findall(r"['\"]clave['\"]\s*:", rep))
    # problemas encontrados
    prob = []
    # deben ser exactamente 6
    if claves != 6:
        # anota cuántos hay
        prob.append(f"{claves} reportes (deben ser 6)")
    # el usuario se pasa como parámetro seguro
    if "%(uid)s" not in rep:
        # anota que falta
        prob.append("sin %(uid)s")
    # un f-string con SELECT/WHERE/FROM = riesgo de inyección SQL
    if re.search(r"\bf['\"].*\b(SELECT|WHERE|FROM)\b", rep, re.IGNORECASE):
        # anota el riesgo
        prob.append("SQL armado con f-string")
    # ok si no hubo problemas
    return ("ok", "6 consultas con %(uid)s") if not prob else ("falla", "; ".join(prob))


def revisar_env():
    """El .env no está en git y sí está en .gitignore."""
    # archivos que git sigue
    seguidos = git("ls-files").splitlines()
    # si algún .env está en git, tus contraseñas están publicadas
    if any(Path(f).name == ".env" for f in seguidos):
        # falla grave: hay que sacarlo con git rm --cached .env
        return "falla", ".env está en el repo: corre  git rm --cached .env  y haz commit"
    # líneas del .gitignore sin espacios
    ignorados = [l.strip() for l in leer(".gitignore").splitlines()]
    # .env debe estar en .gitignore para que no se suba por accidente
    if ".env" not in ignorados:
        # se avisa
        return "revisar", "agrega una línea .env a tu .gitignore"
    # todo bien
    return "ok", "no está en el repo y está en .gitignore"


def revisar_commits(firma):
    """Los commits "paso NN" del 02 al 12, el del 15 y el de evidencias, con tu firma al final."""
    # mensaje de cada commit, del más nuevo al más viejo
    mensajes = git("log", "--format=%s").splitlines()
    # paso → mensaje del commit
    pasos = {}
    # recorre cada mensaje
    for msg in mensajes:
        # ¿empieza con "paso NN"?
        m = re.match(r"\s*paso\s*0?(\d{1,2})\b", msg, re.IGNORECASE)
        # si sí, lo guarda (si hay dos del mismo paso, se queda el más viejo)
        if m:
            # número del paso → mensaje
            pasos[int(m.group(1))] = msg
    # pasos sin commit
    faltan = [f"{p:02d}" for p in PASOS_CON_COMMIT if p not in pasos]
    # ¿ya está el commit final de EVIDENCIAS.md?
    hay_evidencias = any(msg.lower().startswith("evidencias") for msg in mensajes)
    # mensajes que no terminan con " - tu-firma"
    sin_firma = [m for m in pasos.values() if firma and not m.rstrip().endswith("- " + firma)]
    # problemas encontrados
    prob = []
    # pasos sin commit
    if faltan:
        # anota cuáles
        prob.append("sin commit: paso " + ", ".join(faltan))
    # falta el commit 13
    if not hay_evidencias:
        # anota que falta (se hace después de grabar)
        prob.append("falta el commit 'evidencias: minutos del video'")
    # firma mal escrita
    if sin_firma:
        # anota cuántos y el primero de ejemplo
        prob.append(f"{len(sin_firma)} sin tu firma '- {firma}' (ej.: '{sin_firma[0]}')")
    # total de commits que cuentan
    total = len(pasos) + (1 if hay_evidencias else 0)
    # ok, revisar si faltan pocos o falla si faltan muchos
    estado = "ok" if not prob else ("revisar" if len(faltan) <= 3 else "falla")
    # devuelve el punto
    return estado, "; ".join(prob) or f"{total} de 13 commits con tu firma"


def revisar_evidencias():
    """EVIDENCIAS.md: video, Render, minutos llenos y capturas que existen."""
    # texto del archivo
    texto = leer("EVIDENCIAS.md")
    # sin archivo no hay nada que revisar
    if not texto:
        # falla
        return "falla", "no existe EVIDENCIAS.md"
    # problemas encontrados
    prob = []
    # el enlace de Drive debe ser real, no el de ejemplo
    if not re.search(r"^Video:\s*https://drive\.google\.com/\S{10,}", texto, re.MULTILINE):
        # anota que falta
        prob.append("falta el enlace de Drive en 'Video:'")
    # la URL de Render debe ser la de u4p3-…
    if not re.search(r"^Render:\s*https://u4p3-[a-z\-]+\.onrender\.com", texto, re.MULTILINE):
        # anota que falta
        prob.append("falta la URL u4p3-….onrender.com en 'Render:'")
    # filas de la tabla sin minuto
    sin_minuto = []
    # capturas mencionadas que no existen
    sin_captura = []
    # recorre cada línea
    for linea in texto.splitlines():
        # celdas de la fila de la tabla
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        # solo filas que empiezan con número
        if len(celdas) >= 4 and celdas[0].isdigit():
            # sin minuto hh:mm:ss en la tercera celda
            if not MINUTO.search(celdas[2]):
                # anota el número de fila
                sin_minuto.append(celdas[0])
            # cada captura .png de la cuarta celda
            for nombre in re.findall(r"[\w\-/]+\.png", celdas[3]):
                # si no trae carpeta, se busca en evidencias/
                ruta = CARPETA / (nombre if "/" in nombre else "evidencias/" + nombre)
                # anota la que no existe
                if not ruta.exists():
                    # nombre de la captura faltante
                    sin_captura.append(nombre)
    # filas sin minuto
    if sin_minuto:
        # anota cuáles (se llenan después de grabar)
        prob.append("sin minuto: filas " + ", ".join(sin_minuto))
    # capturas faltantes
    if sin_captura:
        # anota cuáles (si son muchas, solo cuántas y las primeras 3)
        prob.append("faltan capturas: " + ", ".join(sin_captura) if len(sin_captura) <= 3 else f"faltan {len(sin_captura)} capturas (ej.: {', '.join(sin_captura[:3])})")
    # ok, revisar si falta poco, o falla si falta mucho
    estado = "ok" if not prob else ("revisar" if len(prob) == 1 and len(sin_minuto) + len(sin_captura) <= 2 else "falla")
    # devuelve el punto
    return estado, "; ".join(prob) or "video, Render, minutos y capturas completos"


def revisar_subido():
    """No hay cambios sin commit ni commits sin push."""
    # archivos cambiados o nuevos que no tienen commit
    cambios = git("status", "--porcelain").splitlines()
    # commits que están en tu compu pero no en GitHub ("" si no hay rama remota)
    pendientes = git("rev-list", "--count", "@{u}..HEAD")
    # problemas encontrados
    prob = []
    # cambios sin commit
    if cambios:
        # anota cuántos
        prob.append(f"{len(cambios)} archivo(s) sin commit (git add . y git commit)")
    # sin rama remota todavía
    if pendientes == "":
        # se avisa
        prob.append("tu rama no está subida (git push -u origin main)")
    # hay commits sin subir
    elif pendientes != "0":
        # anota cuántos
        prob.append(f"{pendientes} commit(s) sin push (git push)")
    # ok si todo está en GitHub
    return ("ok", "todo está en GitHub") if not prob else ("revisar", "; ".join(prob))


def main():
    """Corre todas las revisiones y muestra el resumen."""
    # sin carpeta .git no es un repositorio
    if not (CARPETA / ".git").exists():
        # avisa y termina
        print("❌ Esta carpeta no es un repositorio de git. Copia el kit junto a manage.py.")
        # sale con error
        sys.exit(1)
    # el nombre devuelve también la firma para revisar los commits
    nombre, firma = revisar_nombre()
    # lista de (título, (estado, nota)) en el orden en que se muestran
    puntos = [
        # nombre del repositorio
        ("Nombre del repo", nombre),
        # archivos nuevos
        ("Archivos", revisar_archivos()),
        # migraciones
        ("Migraciones", revisar_migraciones()),
        # consultas SQL
        ("SQL", revisar_sql()),
        # .env fuera del repo
        (".env", revisar_env()),
        # los 13 commits
        ("Commits", revisar_commits(firma)),
        # EVIDENCIAS.md
        ("EVIDENCIAS.md", revisar_evidencias()),
        # todo subido
        ("Subido a GitHub", revisar_subido()),
    ]
    # encabezado
    print("\nRevisión de tu entrega u4p3\n" + "-" * 60)
    # una línea por punto
    for titulo, (estado, nota) in puntos:
        # icono, título alineado y explicación
        print(f"{ICONOS[estado]} {titulo:<16} {nota}")
    # cuántos puntos quedaron en ✅
    ok = sum(1 for _, (estado, _) in puntos if estado == "ok")
    # línea de cierre
    print("-" * 60)
    # mensaje final según el resultado
    if ok == len(puntos):
        # todo listo
        print(f"{ok}/{len(puntos)} ✅  Tu repositorio está listo. Regístralo en apweb.sistemasprado.xyz/repositorio_u4p3")
    else:
        # todavía falta algo
        print(f"{ok}/{len(puntos)} ✅  Corrige los ❌ y ⚠️ y vuelve a correr: python verificar_entrega.py")


# solo corre main() cuando ejecutas el archivo directamente
if __name__ == "__main__":
    # punto de entrada
    main()
