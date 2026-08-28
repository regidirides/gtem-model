// =============================================================================
// GTEM — Manual del usuario (edición en español)
//
// Compilar:  typst compile manual_es.typ GTEM_Manual_ES.pdf
// Vigilar:   typst watch manual_es.typ GTEM_Manual_ES.pdf
//
// Notas de edición para el equipo:
//   - Traducción de manual.typ. Al modificar uno, revise el otro.
//   - Las figuras y las transcripciones se comparten con la edición en inglés.
//   - Las transcripciones de terminal están en inglés porque la consola de GTEM
//     no se traduce. El texto lo explica donde aparecen.
// =============================================================================

#let version = "1.0.0"
#let manual-date = "Agosto de 2026"

#set document(title: "GTEM " + version + " — Manual del usuario",
              author: ("Erick Mas", "Luis Moya", "Jheyder Perez"))

#set page(
  paper: "a4",
  margin: (top: 2.4cm, bottom: 2.2cm, x: 2.3cm),
  numbering: "1",
  number-align: center,
  header: context {
    if counter(page).get().first() > 1 [
      #set text(8pt, fill: luma(120))
      GTEM #version — Manual del usuario
      #h(1fr)
      #counter(page).display()
    ]
  },
  footer: none,
)

#set text(font: ("Helvetica Neue", "Helvetica", "Arial"), size: 10pt, lang: "es")
#set par(justify: true, leading: 0.62em)
#show heading: set block(above: 1.5em, below: 0.9em)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block[
    #set text(20pt, weight: "bold")
    #if it.numbering != none [
      #text(fill: rgb("#1565c0"))[Parte #counter(heading).display()] #linebreak()
    ]
    #it.body
  ]
  line(length: 100%, stroke: 0.6pt + luma(180))
  v(0.4em)
}
#show heading.where(level: 2): set text(14pt, weight: "bold")
#show heading.where(level: 3): set text(11.5pt, weight: "bold")

#show link: it => text(fill: rgb("#1565c0"), it)
#show raw.where(block: false): it => box(
  fill: luma(240), inset: (x: 3pt, y: 0pt), outset: (y: 3pt),
  radius: 2pt, text(9pt, font: "Menlo", it)
)

// ---------------------------------------------------------------- ayudantes ---

#let callout(title, body, colour: rgb("#1565c0"), bg: rgb("#eef4fb")) = block(
  width: 100%, fill: bg, stroke: (left: 3pt + colour),
  inset: 10pt, radius: 2pt, above: 1em, below: 1em,
)[
  #text(weight: "bold", fill: colour)[#title] \
  #body
]

#let warn(title, body) = callout(title, body,
  colour: rgb("#c62828"), bg: rgb("#fdeeee"))

#let tip(title, body) = callout(title, body,
  colour: rgb("#2e7d32"), bg: rgb("#eef7ef"))

#let todo-shot(id, what, why) = block(
  width: 100%, fill: rgb("#fffbe6"), stroke: (paint: rgb("#f9a825"), dash: "dashed", thickness: 1pt),
  inset: 10pt, radius: 3pt, above: 1em, below: 1em,
)[
  #text(weight: "bold", fill: rgb("#b58100"))[CAPTURA #id — pendiente] \
  #text(9.5pt)[*Capturar:* #what] \
  #text(9.5pt, fill: luma(90))[*Por qué:* #why] \
  #v(0.3em)
  #text(8.5pt, style: "italic", fill: luma(110))[
    Guardar como #raw("figures/" + id + ".png") y reemplazar este recuadro por
    #raw("#figure(image(\"figures/" + id + ".png\"), caption: [...])")
    — ver el apéndice al final de este manual.
  ]
]

#let term(path, caption: none) = figure(
  block(width: 100%, fill: luma(28), inset: 9pt, radius: 3pt)[
    #set align(left)
    #set text(8pt, font: "Menlo", fill: rgb("#e8e8e8"))
    #raw(read(path).trim("\n"), block: true)
  ],
  caption: caption, supplement: [Terminal],
)

// ============================================================== portada ===

#page(numbering: none, header: none)[
  #v(2cm)
  #align(center)[
    #image("figures/logo_gtem.png", width: 5.5cm)
    #v(1.2cm)
    #text(30pt, weight: "bold")[GTEM]
    #v(0.1cm)
    #text(15pt)[Modelo Global de Evacuación ante Tsunamis]
    #v(0.5cm)
    #line(length: 45%, stroke: 0.8pt + luma(150))
    #v(0.5cm)
    #text(17pt, weight: "medium")[Manual del usuario]
    #v(0.3cm)
    #text(12pt, fill: luma(90))[Versión #version · #manual-date]
    #v(2.5cm)
    #block(width: 82%)[
      #set text(10.5pt)
      #set par(justify: false)
      Un modelo basado en agentes de la evacuación peatonal ante tsunamis,
      escrito para el personal de gobiernos locales costeros y no para
      especialistas en modelamiento.
    ]
    #v(2.2cm)
    #grid(columns: 3, column-gutter: 1.1cm, align: horizon,
      image("figures/logo_irides.png", width: 3.1cm),
      image("figures/logo_pucp.png", width: 2.2cm),
      image("figures/logo_cdri.png", width: 2.6cm),
    )
    #v(1.4cm)
    #text(9.5pt, fill: luma(90))[
      Erick Mas · Luis Moya · Jheyder Perez \
      Financiado por la Coalition for Disaster Resilient Infrastructure \
      Programa de Becas CDRI 2025–2026
    ]
  ]
]

// ================================================================ contenido ===

#page(numbering: none, header: none)[
  #text(18pt, weight: "bold")[Contenido]
  #v(0.6em)
  #outline(title: none, indent: 1.2em, depth: 2)
]

#counter(page).update(1)

// =============================================================== prefacio =====

#heading(level: 1, numbering: none)[Antes de comenzar]

== Para quién es este manual

No hace falta ser programador ni especialista en modelamiento. El manual supone
que usted sabe instalar programas, abrir una ventana de terminal y editar un
archivo de texto. Todo lo demás se explica aquí.

Si ha usado un sistema de información geográfica como QGIS, la @part-city le
resultará más clara, pero puede ejecutar GTEM en las áreas que vienen incluidas
sin tocar un SIG.

== Qué hace GTEM

Usted le entrega a GTEM tres cosas:

+ una red vial de un área costera,
+ dónde está la gente, y
+ los minutos que transcurren entre el sismo y la llegada de la ola.

GTEM simula a cada persona caminando hacia la zona segura más cercana e informa
quién llega a un lugar seguro a tiempo, quién no, *dónde estaba cuando se le
acabó el tiempo* y qué calles se convirtieron en cuellos de botella.

== Para qué sirve GTEM y para qué no

#warn("Lea esto antes de usar un resultado en una decisión")[
  GTEM es una herramienta para *comparar alternativas*, no para predecir lo que
  va a ocurrir.

  «Abrir esta vía deja a 400 personas menos expuestas» es un uso defendible del
  modelo. «Van a morir 1.847 personas» no lo es.

  GTEM *no ha sido validado contra una evacuación observada.* Hasta que lo
  esté, considere provisional toda cifra absoluta. La declaración completa de
  lo que el modelo puede y no puede responder está en `docs/LIMITATIONS.md`, y
  conviene leerla antes de presentar resultados a nadie.
]

== Cómo usar este manual

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 7pt,
  table.header([*Si quiere…*], [*Lea*]),
  [instalar GTEM y verlo funcionar], [@part-start],
  [entender qué significan los resultados], [@part-results],
  [realizar estudios realistas], [@part-scenarios],
  [usar GTEM en su propia ciudad], [@part-city],
  [saber cómo funciona el modelo por dentro], [@part-model],
  [consultar algo puntual], [@part-reference],
)

#tip("Una nota sobre los comandos")[
  Todo lo que aparece en un recuadro oscuro se escribe en una terminal. Escriba
  el comando, presione Enter y compare lo que ve con lo que muestra el manual.
  En un archivo de configuración, el texto que sigue a un `#` es un comentario y
  se ignora.
]

#tip("El idioma de los resultados y el de la consola")[
  GTEM escribe las figuras y los informes PDF en español cuando se lo indica
  (@sec-idioma). En cambio, los mensajes de la consola y las advertencias del
  motor de simulación están solo en inglés, de modo que las transcripciones de
  terminal de este manual aparecen tal como las verá en su pantalla.
]

// ========================================================= PARTE I: INICIO ====

= Primeros pasos <part-start>

== Qué necesita

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Elemento*], [*Notas*]),
  [Una computadora con Windows 10/11, macOS o Linux],
    [Cualquier equipo de los últimos años basta. Una corrida completa de un área
     de 17.000 personas toma unos 90 segundos.],
  [NetLogo 7.0.4], [Gratuito. Es el motor de simulación que GTEM controla. Java
     viene incluido: *no* necesita instalarlo aparte.],
  [Miniforge, Miniconda o Anaconda], [Gratuito. Sirve para instalar los paquetes
     de Python que GTEM necesita sin alterar nada más en su equipo.],
  [Alrededor de 1 GB de espacio libre], [La descarga es pequeña; los resultados
     se acumulan.],
)

== Instalación

=== Paso 1 — Instalar NetLogo

Descargue NetLogo 7.0.4 desde #link("https://ccl.northwestern.edu/netlogo/")[ccl.northwestern.edu/netlogo]
e instálelo en la ubicación predeterminada.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Sistema*], [*Ubicación donde GTEM lo busca*]),
  [Windows], [`C:\Program Files\NetLogo 7.0.4`],
  [macOS], [`/Applications/NetLogo 7.0.4`],
  [Linux], [`/opt/netlogo-7.0.4`],
)

Si lo instala en otro lugar, defina una variable de entorno llamada
`NETLOGO_HOME` que apunte a esa carpeta. GTEM le avisará si no encuentra NetLogo
y le mostrará los lugares donde buscó.

#todo-shot("S1",
  [La página de descarga de NetLogo, con el botón de descarga de la versión
   7.0.4 visible.],
  [Los usuarios nuevos suelen descargar la versión más reciente en lugar de la
   7.0.4. Una imagen del botón correcto evita el error de instalación más
   frecuente.])

=== Paso 2 — Obtener GTEM

Descargue o clone la carpeta de GTEM y colóquela en una ruta corta: por ejemplo
`C:\GTEM` en Windows, o su carpeta personal en macOS o Linux.

#warn("Evite rutas de carpeta largas en Windows")[
  Windows tiene un límite de 260 caracteres para las rutas de archivo. GTEM
  escribe los resultados en carpetas anidadas, de modo que ubicarlo dentro de
  una ruta muy profunda como
  `C:\Users\...\OneDrive\Documents\Proyectos\2026\...` puede provocar errores
  que parecen no tener relación. Una ruta corta evita el problema por completo.
]

#todo-shot("S2",
  [La carpeta de GTEM ya descomprimida, abierta en el Explorador de Windows o en
   el Finder de macOS, mostrando `main.py`, `data`, `examples`, `docs` y `src`.],
  [Confirma que el lector descomprimió al nivel correcto. Un error habitual es
   quedarse con una carpeta que solo contiene otra carpeta.])

=== Paso 3 — Crear el entorno

Abra una terminal. En Windows es el *Miniforge Prompt* o el *Anaconda Prompt*
del menú Inicio, no el Símbolo del sistema común. Ubíquese en la carpeta de GTEM
y ejecute:

```bash
conda env create -f environment.yml
conda activate gtem
```

El primer comando descarga e instala todo lo que GTEM necesita y demora algunos
minutos. El segundo cambia su terminal a ese entorno.

#warn("En una Mac con Apple Silicon, el entorno debe ser arm64")[
  NetLogo incluye un motor Java arm64 en Apple Silicon, y una versión Intel de
  Python no puede cargarlo. La corrida falla entonces con `JVM DLL not found`,
  nombrando un archivo que sí existe.

  Anaconda instalado en `/opt/anaconda3` suele ser la versión Intel y crea
  entornos Intel por omisión. Instale Miniforge, que es arm64, o fuerce la
  arquitectura:

  ```bash
  CONDA_SUBDIR=osx-arm64 conda env create -f environment.yml
  conda activate gtem
  conda config --env --set subdir osx-arm64
  ```

  `python check_environment.py` informa la arquitectura de ambos, de modo que
  usted verá esto antes de ejecutar una simulación y no después.
]

#tip("Debe activar el entorno en cada terminal nueva")[
  `conda activate gtem` solo se aplica a la ventana donde lo escribe. Si cierra
  la terminal y abre otra, vuelva a ejecutarlo. Si de pronto un comando informa
  que falta un paquete, casi siempre esta es la razón.
]

#todo-shot("S3",
  [El Miniforge Prompt en Windows justo después de `conda activate gtem`, con el
   prefijo `(gtem)` al inicio de la línea.],
  [El prefijo `(gtem)` es la confirmación visual de que el entorno está activo.
   Quien no lo advierte se topa después con errores confusos.])

== Comprobar que funcionó

Ejecute:

```bash
python check_environment.py
```

Esto importa cada paquete que GTEM necesita, localiza NetLogo y confirma que el
modelo y los datos están presentes. Debería ver algo muy parecido a esto:

#term("transcripts/check_environment.txt",
  caption: [`check_environment.py` en un equipo correctamente instalado. La
            consola de GTEM está en inglés.])

Si algo está mal, la herramienta imprime el comando exacto para corregirlo y
termina con error. La comprobación se hace *importando* cada paquete y no solo
buscándolo en el disco, porque un paquete puede estar presente y aun así no
cargar.

== Su primera corrida

Empiece con el área de prueba incorporada `Synthetic_Corridor`. Es
deliberadamente artificial: dos corredores rectos de 1.000 metros, cada uno con
una zona segura al final. Una persona que camina a la velocidad de flujo libre
de 1,33 m/s recorre 1.000 m en *12,53 minutos*, así que usted sabe de antemano
cuál debe ser la respuesta.

Cree un archivo llamado `mi_primera_corrida.txt` con este contenido:

```
zone              = Synthetic_Corridor
adults            = 50
elderly           = 0
children          = 0
tsunami_eta       = 30
departure_mean    = 0
dt                = 5
seed              = 1
recompute_routes  = true
language          = es
```

Luego ejecute:

```bash
python main.py --config mi_primera_corrida.txt
```

La corrida termina en menos de un minuto y concluye con todos a salvo alrededor
de los 12,5 minutos, coincidiendo con el cálculo a mano. Si ve eso, GTEM
funciona correctamente en su equipo.

Los resultados se escriben en `Outputs/Synthetic_Corridor/1/`. Abra primero el
PDF.

#todo-shot("S4",
  [La carpeta `Outputs/Synthetic_Corridor/1/` mostrando los 14 archivos de
   salida.],
  [Muestra al lector dónde aparecen los resultados y cómo luce un conjunto
   completo, para que note de un vistazo si falta algo.])

== Un área real

Ahora ejecute una de las áreas de estudio peruanas incluidas. Primero revise sus
datos:

```bash
python check_inputs.py Chimbote_Zona1
```

#term("transcripts/check_inputs.txt",
  caption: [Revisión de un área de estudio real. Las advertencias son normales:
            los datos reales rara vez son perfectos. Lo importante es leerlas.])

Luego ejecútela:

```bash
python main.py --config examples/config_example.txt --language es
```

Esto simula 17.261 personas con un tiempo de llegada del tsunami de 23 minutos y
demora unos 90 segundos.

// ======================================================= PARTE II: RESULTADOS ==

= Cómo leer sus resultados <part-results>

Cada corrida escribe catorce archivos en `Outputs/<área>/<semilla>/`. Empiece por
el PDF; los archivos CSV están ahí cuando necesite las cifras que hay detrás.

== Las cuatro cifras que importan

Aparecen en la página 1 del PDF y en `Run_Summary.csv`.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Cifra*], [*Qué significa*]),
  [*Evacuados antes del tsunami*],
    [Llegaron a una zona segura *antes* de la ola. Son las únicas personas
     realmente a salvo.],
  [*NO evacuados*],
    [Todos los demás. Mire siempre esta cifra, no solo la primera.],
  [*Sorprendidos en tránsito*],
    [Seguían caminando cuando llegó la ola. Suele mejorar con una salida más
     temprana o con zonas seguras más cercanas.],
  [*Sin ruta de evacuación*],
    [No tenían ningún camino hacia una zona segura desde donde partieron, ya
     antes de que empezara la simulación. Es un problema de *red vial*, no de
     conducta. Ninguna cantidad de preparación ni de tiempo de alerta lo
     resuelve.],
)

Los tres resultados siempre suman la cantidad de personas simuladas. GTEM lo
verifica mientras corre: si alguna vez no cuadraran, la corrida se detendría con
un error en lugar de informar una cifra que deja gente fuera.

#warn("Llegar a una zona segura después de la ola no es estar a salvo")[
  GTEM detiene la simulación en el momento de llegada del tsunami. Quien siga
  caminando se cuenta como *no evacuado*, por cerca que estuviera. Es
  deliberado: un modelo que cuenta como sobrevivientes a quienes llegan tarde
  halaga al plan que se está evaluando.
]

== Las cinco figuras

=== Figura 1 — Avance de la evacuación por grupo de edad

#figure(image("figures/fig_dynamics_es.png", width: 82%),
  caption: [Cada grupo de edad tiene su propio panel, expresado como porcentaje
            de ese grupo. La línea roja vertical es la hora de llegada del
            tsunami.])

*Qué observar.* Compare los tres paneles. En el ejemplo, los adultos alcanzan el
70,3% pero los adultos mayores solo el 51,7%: una brecha de casi 19 puntos. Esa
brecha es un hallazgo accionable: apunta a evacuación asistida o a difusión
focalizada, no a más señalización.

Todo lo que queda a la derecha de la línea roja no ocurrió a tiempo.

=== Figura 2 — Velocidad de caminata por grupo de edad

#figure(image("figures/fig_speed_es.png", width: 82%),
  caption: [Velocidad media de caminata de cada grupo. La línea punteada es la
            velocidad de flujo libre de ese grupo, es decir, la velocidad con la
            calle para sí solo.])

*Qué observar.* Una curva pegada a la línea punteada significa que la gente
camina sin obstáculos. Una curva que se aleja de ella indica aglomeración. En el
ejemplo, los tres grupos caen bruscamente después del minuto 12: es la
congestión acumulándose en los accesos a las zonas seguras, no gente que se
cansa; GTEM no modela la fatiga.

=== Figura 3 — Vulnerabilidad según el punto de partida

#figure(image("figures/fig_vulnerability_es.png", width: 80%),
  caption: [Dónde *partió* cada persona, coloreado según cuánto tardó en llegar
            a un lugar seguro. Los puntos negros nunca llegaron.])

*Qué observar.* Los grupos de puntos negros. Son las áreas prioritarias: lugares
donde la evacuación *fracasa*, no simplemente donde es lenta. En el ejemplo,
todo el distrito suroeste aparece en negro.

#tip("Este mapa muestra a todos, incluidas las personas que no lo lograron")[
  Un área en blanco en este mapa significa que nadie partió de allí. *No*
  significa que todos allí estuvieran a salvo. Los lugares donde la evacuación
  fracasó se dibujan en negro precisamente para que no puedan confundirse con
  espacio vacío.
]

=== Figura 4 — Demanda sobre cada zona segura

#figure(image("figures/fig_safezones_es.png", width: 78%),
  caption: [El tamaño y el color del marcador indican cuántas personas llegaron.
            Las más cargadas están rotuladas.])

*Qué observar.* Dos cosas.

Primero, la *concentración*. En el ejemplo, una zona segura recibe 4.808
personas mientras otra no recibe a nadie. GTEM envía a todos a la zona segura
más cercana por distancia, de modo que la demanda se acumula donde esa regla
apunte.

Segundo, la *capacidad*. GTEM supone que las zonas seguras son de tamaño
ilimitado. No le advertirá que una plaza habilitada para 500 personas recibió
1.200. Contrastar las cifras de esta figura con la capacidad real de cada sitio
es un paso manual, y es importante.

Una zona segura que no recibe a nadie merece revisión: puede ser inaccesible,
estar mal ubicada o sencillamente sobrar.

=== Figura 5 — Congestión de las calles

#figure(image("figures/fig_congestion_es.png", width: 82%),
  caption: [Calles ordenadas por aglomeración acumulada en el tiempo, con los
            diez tramos más críticos numerados y listados.])

*Qué observar.* La lista ordenada nombra las calles por el par de intersecciones
en sus extremos. Son los tramos donde ensanchar, despejar obstáculos o señalizar
una alternativa ahorraría más tiempo.

Aquí la criticidad es la aglomeración *acumulada*, no el peor instante. Una
calle brevemente muy concurrida queda por debajo de otra moderadamente
congestionada durante muchos minutos, porque la segunda demora a mucha más
gente.

== Los demás archivos

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Archivo*], [*Contenido*]),
  [`Run_Summary.csv`], [Una fila: todas las cifras principales de esta corrida.],
  [`Report1_Dynamics.csv`], [La curva de evacuación, minuto a minuto.],
  [`Report2_Speeds.csv`], [Velocidad media por grupo de edad en el tiempo.],
  [`Report3_Vulnerability.csv`], [Una fila por persona: dónde partió, cuánto
     tardó y cuál fue su resultado.],
  [`Report4_SafeZones.csv`], [Llegadas a cada zona segura.],
  [`Report5_Congestion.csv`], [Todas las calles, ordenadas por aglomeración
     acumulada.],
  [`resolved_config.txt`], [Todos los valores realmente usados, incluidos los
     predeterminados que usted no escribió. Consérvelo: es lo que hace
     reproducible un resultado.],
  [`warnings.log`], [Problemas detectados en sus datos de entrada. Ver abajo.],
)

#tip("Los nombres de archivo y los encabezados de columna no se traducen")[
  Son iguales en todos los idiomas, a propósito, para que dos corridas puedan
  compararse columna por columna sin importar en qué idioma se escribieron sus
  informes, y para que un script escrito sobre sus resultados siga funcionando
  cuando un colega ejecute el modelo en el otro idioma.
]

== Lea siempre `warnings.log`

Cada corrida lo escribe, y el mismo contenido aparece en el PDF. Informa lo que
GTEM encontró mal en sus *datos de entrada*, no en la simulación.

Cuando no hay nada que informar, dice `No input warnings.` de forma explícita,
de modo que el silencio siempre significa «revisado y limpio» y nunca «no
revisado».

En el área de Chimbote incluida aparecen cinco advertencias. La más grave es:

#block(fill: rgb("#fffbe6"), inset: 9pt, radius: 3pt, width: 100%)[
  #text(9pt, font: "Menlo")[
    DISCONNECTED NETWORK: 884 of 4468 road nodes (19.8%) have no route to any
    safe zone. Anyone starting there is counted as stranded.
  ]
]

Es decir: 884 de 4.468 nodos viales (19,8%) no tienen ruta hacia ninguna zona
segura, y quien parta de allí se cuenta como sin ruta. Casi la quinta parte de
esa red vial no puede llegar a un lugar seguro. Ese es un hallazgo sobre la
*ciudad*, y merece atención antes de sacar cualquier conclusión sobre conducta o
tiempos de alerta.

#tip("Las advertencias del motor están solo en inglés")[
  Las genera el motor de simulación, que no se traduce. El informe en español lo
  señala en la página donde aparecen.
]

== Una sola corrida no es un resultado

GTEM es estocástico: los tiempos de salida y las posiciones iniciales se sortean
al azar. Dos corridas con semillas distintas dan respuestas distintas. En 100
réplicas de un escenario de Chimbote, las corridas individuales fueron desde el
80,1% hasta el 84,5% evacuado: una dispersión de más de cuatro puntos
porcentuales debida solo al azar.

#warn("Nunca cite una sola corrida")[
  Ejecute réplicas e informe el promedio con su dispersión. La @part-scenarios
  explica cómo, y cuántas réplicas necesita. Una sola corrida le dice cómo fue
  una tarde posible, no lo que la ciudad puede esperar.
]

// ===================================================== PARTE III: ESCENARIOS ===

= Cómo realizar estudios reales <part-scenarios>

== El archivo de configuración

Todos los valores viven en un archivo de texto simple. Usted nunca edita un
archivo de Python.

Copie `examples/config_example.txt`, edite la copia y pásela con `--config`.
Cada línea es `parámetro = valor`; lo que sigue a un `#` es un comentario.

=== Valores que usted debe indicar

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Parámetro*], [*Ejemplo*], [*Significado*]),
  [`zone`], [`Chimbote_Zona1`],
    [Nombre de la carpeta dentro de `data/`. Debe coincidir exactamente,
     incluidas las mayúsculas.],
  [`adults`], [`11328`], [Cantidad de adultos a simular.],
  [`elderly`], [`1917`], [Cantidad de adultos mayores.],
  [`children`], [`4016`], [Cantidad de niños.],
  [`tsunami_eta`], [`23`],
    [*La cifra más importante de todas.* Minutos desde el sismo hasta la llegada
     de la ola. La simulación se detiene aquí.],
)

=== Valores con predeterminados razonables

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Parámetro*], [*Predeterminado*], [*Significado*]),
  [`departure_mean`], [`7`],
    [Minutos promedio antes de que una persona empiece a moverse. Es el supuesto
     de conducta más influyente del modelo.],
  [`dt`], [`10`],
    [Segundos de tiempo simulado por paso. Debe ser mayor que 0 y como máximo
     10. Más pequeño es más preciso y más lento.],
  [`end_of_simulation`], [`0`],
    [Corte adicional en minutos. `0` significa «detenerse en la hora de llegada
     del tsunami», que es casi siempre lo que usted quiere.],
  [`road_width`], [`2.8`], [Ancho útil de un carril, en metros.],
  [`capacity_multiplier`], [`1`],
    [Escala el ancho vial efectivo. `1` es sin daños; `0.5` es la mitad.],
  [`max_snap_distance`], [`50`],
    [Distancia máxima a la que una persona puede partir de la red vial antes de
     que se informe.],
  [`vulnerability_low` / `_high`], [`11` / `17`],
    [Bandas de color del mapa de vulnerabilidad, en minutos.],
  [`density_low` / `_high`], [`0.3` / `3`],
    [Bandas de color de la congestión, en personas por metro cuadrado.],
  [`seed`], [`0`],
    [`0` sortea una semilla y la registra. Cualquier otro número reproduce esa
     corrida exacta.],
  [`recompute_routes`], [`false`],
    [Reconstruye la tabla de rutas. Solo hace falta cuando cambia la red vial.],
  [`time_margin_analysis`], [`false`],
    [Mide cuánto tiempo más necesitaría una evacuación completa. Duplica
     aproximadamente la duración. Ver la @sec-margin.],
  [`language`], [`en`],
    [Idioma de las figuras y del informe PDF: `en` o `es`. Ver la @sec-idioma.],
  [`record_video`], [`false`],
    [Graba un MP4. Lento, y genera un archivo grande.],
)

#todo-shot("S5",
  [Un archivo de configuración abierto en un editor de texto (Bloc de notas,
   TextEdit o VS Code), con un par de valores resaltados.],
  [Muchos lectores nunca han editado un archivo de configuración de texto simple
   y no saben qué significa «edite la copia» en la práctica.])

== Cuando algo está mal

GTEM se niega a correr antes que producir una respuesta plausible pero errónea.
Cada rechazo nombra el parámetro y el rango aceptable:

#term("transcripts/error_invalid_dt.txt",
  caption: [Una configuración rechazada. No se escribe nada; no hay nada que
            limpiar después.])

Ninguna entrada inválida genera jamás una carpeta de salida que pudiera
confundirse con un resultado. Si una corrida falla a mitad de camino, GTEM deja
un archivo llamado `FAILED.txt` en la carpeta de salida, de modo que una carpeta
a medio terminar nunca pueda leerse como una terminada.

== Réplicas: ¿cuántas corridas necesita? <sec-replicates>

Como el modelo es estocástico, un resultado defendible es un *promedio sobre
réplicas*. Las corridas por lote lo hacen por usted.

Edite `examples/scenario_list.csv`. Cada fila es un escenario; la columna
`Count` indica cuántas réplicas ejecutar:

```
Zone,Adults,Elderly,Children,TR,Count,Vuln_Low,Vuln_High,Tsunami_ETA,...
Chimbote_Zona1,11328,1917,4016,7,40,11,17,23,...
```

Luego:

```bash
python batch_main.py --input examples/scenario_list.csv --seed 2026 --workers 4 --language es
```

`--seed` hace reproducible todo el lote. `--workers` fija cuántas corridas se
ejecutan a la vez; cada una necesita su propio proceso de Java, así que empiece
con 2 a 4.

=== Qué produce un lote

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Archivo*], [*Contenido*]),
  [*`Batch_Report.pdf`*],
    [*Empiece aquí.* Promedios con su dispersión, una comparación entre
     escenarios y un veredicto explícito sobre si ejecutó suficientes réplicas.],
  [`Aggregated_Summary.csv`], [Promedio, desviación estándar y cantidad por
     escenario.],
  [`Master_Summary.csv`], [Una fila por corrida individual.],
  [`Convergence.csv`, `Figure_Convergence.png`],
    [Cómo se estabilizó la estimación a medida que se acumularon las réplicas.],
  [`Convergence_Summary.txt`],
    [La cantidad de réplicas necesaria para una precisión determinada.],
)

=== ¿Cuántas son suficientes?

GTEM responde esto a partir de sus propios datos en lugar de pedirle que
adivine. Acumula el coeficiente de variación desde la corrida 1 en adelante
—corridas 1–2, 1–3, 1–4 y así— e informa dónde se estabiliza.

En el área de referencia, dos criterios independientes coinciden en unas *40
réplicas*:

#table(
  columns: (1fr, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Criterio*], [*Réplicas*]),
  [El coeficiente de variación se mantiene dentro del 10% de su valor final], [40],
  [Intervalo de confianza del 95% del promedio dentro de ±0,25 puntos porcentuales], [41],
  [Intervalo de confianza del 95% dentro de ±0,50 puntos porcentuales], [11],
  [Intervalo de confianza del 95% dentro de ±0,10 puntos porcentuales], [256],
)

El informe del lote dice con todas sus letras cuándo un lote fue *demasiado
pequeño*, y nombra los escenarios cuyas estimaciones no se han estabilizado.
Tómelo en serio: es la diferencia entre un resultado y una anécdota.

=== Cómo se ve un lote sin terminar

#figure(
  image("figures/fig_convergence_es.png", width: 88%),
  caption: [`Figure_Convergence.png` de un lote deliberadamente corto, de 14
    réplicas. La curva sigue moviéndose en el extremo derecho y
    `Convergence_Summary.txt` informa
    #raw("El CV se estabiliza en n = no alcanzado").
    La estimación no se ha estabilizado.],
)

Una curva convergida se aplana y se mantiene plana. Si la suya todavía sube,
baja o salta en el extremo derecho, el lote es demasiado pequeño, diga lo que
diga el promedio. En el lote de arriba, la precisión alcanzada fue de ±0,661
puntos porcentuales, y llegar a ±0,25 requeriría 98 réplicas.

== ¿Cuánto tiempo faltó? <sec-margin>

Una corrida limitada por la hora de llegada del tsunami puede decirle que la
ciudad se quedó sin tiempo, pero no por cuánto. Fijar
`time_margin_analysis = true` repite la simulación una vez con la misma semilla
y sin límite de tiempo, y agrega una sección al informe:

#block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
  #text(9.5pt)[
    En el área de referencia, una evacuación completa necesita *56,7 minutos*.
    La ola llega a los *23,0 minutos*. El déficit es de *33,7 minutos*.
  ]
  #v(0.4em)
  #table(
    columns: (auto, auto, auto, auto), stroke: 0.4pt + luma(200), inset: 5pt,
    align: (left, right, right, right),
    table.header([Tiempo adicional], [Llegaron a salvo], [Personas adicionales],
                 [Porcentaje]),
    [+1 min], [11.846], [573], [3,3%],
    [+2 min], [12.295], [1.022], [5,9%],
    [+3 min], [12.853], [1.580], [9,2%],
    [+5 min], [13.862], [2.589], [15,0%],
    [+10 min], [15.505], [4.232], [24,5%],
  )
]

Alrededor de 500 personas por cada minuto adicional. Como el modelo trata por
igual una alerta más larga y una salida más temprana, esta tabla también mide
cuánto vale la *preparación*: convencer a la gente de salir dos minutos antes
tiene el mismo efecto que dos minutos más de alerta.

== Comparación de escenarios

La comparación es el uso más sólido de GTEM, porque ambos escenarios comparten
los mismos supuestos y buena parte de la incertidumbre se cancela.

Las áreas incluidas traen un ejemplo trabajado: `Chimbote_Zona1` y
`Chimbote_Zona1_colapso1`, la misma ciudad con daño sísmico en la red vial.
Ponga ambas en un mismo archivo de escenarios y ejecútelas juntas.

Diez réplicas de cada una, con la población completa de 17.261 personas:

#table(
  columns: (1fr, auto, auto, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  align: (left, right, right, right),
  table.header([*Escenario*], [*Evacuado (promedio ± DE)*], [*Sin ruta*],
               [*Diferencia*]),
  [Chimbote_Zona1], [64,95% ± 0,72], [0], [referencia],
  [Chimbote_Zona1_colapso1], [29,50% ± 0,43], [7.194], [−35,45 puntos],
)

La columna `Sin ruta` explica el mecanismo, y es el hallazgo más útil. El daño
vial no solo hace más lenta a la gente: deja a 7.194 personas incomunicadas de
toda zona segura. A esas personas no las ayuda más tiempo de alerta. Necesitan
una ruta que sobreviva al sismo, o una zona segura de su lado del daño.

#tip("Cómo distinguir una diferencia real del ruido")[
  Compare la diferencia con las desviaciones estándar. Aquí la brecha es de
  35,45 puntos frente a dispersiones menores a un punto, así que la diferencia
  es inequívocamente real. Una diferencia *menor* que la dispersión es
  indistinguible de la suerte de la semilla aleatoria, y no debe informarse como
  un hallazgo.
]

Tenga presente que diez réplicas bastaron para establecer *esta* diferencia,
pero no para fijar con precisión ninguno de los dos promedios: el
`Convergence_Summary.txt` de ese lote pide 32 réplicas del escenario de
referencia para alcanzar ±0,25 puntos porcentuales. Una diferencia grande
necesita menos réplicas que una cifra absoluta precisa.

// ==================================================== PARTE IV: SU CIUDAD =====

= Usar GTEM en su propia ciudad <part-city>

Esta es la parte más exigente del trabajo. GTEM todavía no arma un área de
estudio por usted: usted ensambla cuatro capas cartográficas en un SIG y GTEM
las revisa.

Reserve algunas horas la primera vez. La segunda ciudad es mucho más rápida.

== Qué necesita GTEM

Cuatro shapefiles, en una carpeta con el nombre de su área, dentro de `data/`:

```
data/Mi_Ciudad_Zona1/
    Mi_Ciudad_Zona1.shp            límite de la zona     (polígono)
    puntos_Mi_Ciudad_Zona1.shp     intersecciones        (puntos)
    rutas_Mi_Ciudad_Zona1.shp      red vial              (líneas)
    manzanas_Mi_Ciudad_Zona1.shp   manzanas censales     (polígonos)
```

#tip("Por qué los nombres de archivo están en español")[
  `puntos`, `rutas` y `manzanas` se conservaron porque las contrapartes del
  proyecto ya manejan sus datos con esos nombres. Son solo nombres de archivo:
  el interior de GTEM está en inglés, incluidos los nombres de los parámetros y
  los encabezados de columna.
]

Cada `.shp` necesita sus archivos acompañantes (`.dbf`, `.shx`, `.prj`, `.cpg`)
junto a él. Cópielos todos.

== Primero, acierte con el sistema de coordenadas

#warn("Un sistema de coordenadas geográficas será rechazado")[
  Todas las capas deben usar el mismo sistema de referencia de coordenadas
  *proyectado y métrico*, normalmente una zona UTM. GTEM mide distancias en
  metros.

  Si usted entrega latitud y longitud (EPSG:4326, que suele aparecer como
  «WGS 84»), las distancias se medirían en *grados* y todo resultado carecería
  de sentido. GTEM se niega a correr antes que permitirlo.

  En QGIS: *Capa ▸ Exportar ▸ Guardar objetos como…*, y fije allí el SRC.
]

#todo-shot("S6",
  [El cuadro de diálogo *Guardar objetos como…* de QGIS, con el selector de SRC
   mostrando una zona UTM.],
  [La reproyección es el error de preparación más frecuente, y el cuadro de
   diálogo no es evidente para quien lo usa por primera vez.])

== Qué debe contener cada capa

=== Límite de la zona — `<zona>.shp`

Un polígono que cubra el área de estudio. GTEM solo usa su extensión, así que un
rectángulo sirve. No hace falta ningún atributo.

Manténgalo ajustado: la extensión fija la resolución espacial, de modo que un
límite con un amplio margen vacío la desperdicia.

=== Intersecciones — `puntos_<zona>.shp`

Puntos donde se encuentran las vías, más las zonas seguras. Son los nodos de la
red.

#table(
  columns: (auto, auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Atributo*], [*Tipo*], [*Obligatorio*], [*Significado*]),
  [`fid`], [entero], [sí],
    [Identificador único. Los duplicados provocan errores silenciosos que
     dependen de la semilla.],
  [`is_shelter`], [entero], [sí],
    [`1` marca una zona segura; `0`, una intersección común.],
  [`name`], [texto], [opcional],
    [Un nombre legible como «Colegio San Pedro». Se usa para rotular las zonas
     seguras más cargadas; sin él se rotulan por número.],
)

#warn("Decidir qué cuenta como zona segura es su criterio, no un conjunto de datos")[
  GTEM no lee un mapa de inundación. Simplemente confía en sus marcas
  `is_shelter`. Esa única decisión gobierna todo el resultado, así que debería
  provenir de su mapa de peligro y de su plan de protección civil.

  Al menos un punto debe tener `is_shelter = 1`, o nadie podrá evacuar: GTEM se
  detiene con un error en lugar de informar que murieron todos.
]

=== Red vial — `rutas_<zona>.shp`

Una línea por tramo de calle, que une dos intersecciones.

#table(
  columns: (auto, auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Atributo*], [*Tipo*], [*Obligatorio*], [*Significado*]),
  [`start_node`], [entero], [sí], [`fid` de la intersección de un extremo.],
  [`end_node`], [entero], [sí], [`fid` de la intersección del otro extremo.],
  [`cost`], [número], [sí],
    [Longitud en *metros*, siguiendo la calle y no la línea recta.],
  [`lanes`], [entero], [sí],
    [Cantidad de carriles. Se multiplica por `road_width` para obtener el ancho
     transitable, que determina la aglomeración. Un pasaje angosto es `1`.],
)

Evite tramos de menos de un metro: una sola persona en un tramo de 0,1 m produce
una densidad absurda y un falso punto crítico de congestión.
`check_inputs.py` los cuenta por usted.

=== Manzanas censales — `manzanas_<zona>.shp`

Polígonos donde parte la gente. GTEM distribuye personas dentro de ellos en
proporción a la población.

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Atributo*], [*Obligatorio*], [*Significado*]),
  [`T_TOTAL`], [muy recomendable],
    [Población residente de la manzana. También se aceptan `Population` y
     `POP`.],
)

#warn("Sin un atributo de población los resultados valen poco")[
  GTEM igual correrá, repartiendo a la gente de forma *uniforme* e ignorando
  dónde vive realmente. Lo dice con claridad en `warnings.log` y en el informe.
  Este es el error de preparación más frecuente.
]

Recorte las manzanas al área en riesgo. GTEM crea personas dondequiera que usted
entregue una manzana, así que una capa sin recortar simula gente que nunca
estuvo en peligro.

== De dónde obtener los datos

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Capa*], [*Fuentes abiertas*]),
  [Red vial],
    [OpenStreetMap, mediante el complemento QuickOSM de QGIS, los extractos de
     Geofabrik o de Overpass. El catastro municipal, si dispone de él.],
  [Intersecciones], [Se derivan de la red vial; ver más abajo.],
  [Manzanas censales],
    [Su instituto nacional de estadística (INEI en Perú, INE en Chile, e-Stat en
     Japón, IBGE en Brasil, BPS en Indonesia, Eurostat en la UE). Alternativas
     globales: WorldPop, la Global Human Settlement Layer o la High Resolution
     Settlement Layer de Meta, a través del Humanitarian Data Exchange.],
  [Límite de la zona],
    [Dibújelo usted mismo, o use un límite administrativo de OpenStreetMap o de
     GADM.],
  [Hora de llegada del tsunami],
    [Su organismo nacional de alerta de tsunamis (DHN en Perú, JMA en Japón,
     SHOA en Chile), estudios nacionales de peligro, o la base de datos
     histórica de tsunamis de la NOAA.],
  [Extensión de la inundación],
    [Mapas nacionales de peligro. En su defecto, un umbral de elevación
     conservador tomado de un modelo digital de elevación gratuito: Copernicus
     DEM GLO-30, NASADEM o ALOS World 3D.],
)

== Cómo construir las capas en QGIS

+ *Fije el sistema de coordenadas del proyecto* a su SRC métrico antes que nada.
+ *Cargue una capa de ejes viales*: datos municipales, o OpenStreetMap a través
  del complemento QuickOSM.
+ *Recorte las vías* a su área de estudio.
+ *Divida las líneas en las intersecciones*, apuntando a tramos de unos 10 a
  25 m.
+ *Extraiga los vértices* (*Vectorial ▸ Herramientas de geometría ▸ Extraer
  vértices*) y elimine los duplicados. Esto se convierte en `puntos_`.
+ *Agregue `fid`* como entero único en los puntos.
+ *Una los identificadores de nodo a las líneas*, usando *Unir atributos por el
  más cercano* dos veces, una por cada extremo, para llenar `start_node` y
  `end_node`.
+ *Agregue `cost`* con la calculadora de campos: `$length`. Confirme que las
  unidades sean metros.
+ *Agregue `lanes`*, con valor 1 por defecto, aumentándolo en las vías
  principales.
+ *Marque las zonas seguras*: fije `is_shelter = 1` en los puntos fuera del área
  de inundación o en edificios de evacuación vertical. Agregue `name` si puede.
+ *Prepare las manzanas censales* con una columna de población, recortadas al
  área en riesgo.
+ *Exporte las cuatro capas* a `data/<zona>/` con los nombres requeridos.

#todo-shot("S7",
  [*Extraer vértices* de QGIS ejecutándose sobre la capa vial, con el resultado
   visible.],
  [El paso 5 es donde la mayoría se pierde. Una imagen de la ruta del menú y de
   la capa de puntos resultante elimina la ambigüedad.])

#todo-shot("S8",
  [La calculadora de campos de QGIS creando `cost` con la expresión `$length`.],
  [Muestra a la vez dónde está la calculadora y cómo se ve la expresión.])

#todo-shot("S9",
  [La tabla de atributos de `puntos_` con `fid` e `is_shelter` visibles, y al
   menos una fila donde `is_shelter` valga 1.],
  [El lector necesita ver que `is_shelter` es una columna entera común que él
   edita a mano, no algo que GTEM calcule.])

== Revise antes de simular

```bash
python check_inputs.py Mi_Ciudad_Zona1
```

Este es el paso que convierte una falla confusa a mitad de simulación en una
lista de verificación. Ejecútelo cada vez que cambie los datos.

Así se ve sobre un área deliberadamente defectuosa que viene con GTEM:

#term("transcripts/check_inputs_broken.txt",
  caption: [`Synthetic_Broken` viene incluida para que usted vea cómo luce una
            carpeta defectuosa antes de encontrarse con una propia.])

=== Qué significan los mensajes

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Mensaje*], [*Qué hacer*]),
  [`geographic CRS`], [Reproyecte todas las capas a UTM. Nada más importa hasta
     corregir esto.],
  [`missing start_node`], [La unión del paso 7 no se ejecutó, o produjo una
     columna con otro nombre.],
  [`no safe zones`], [Ningún punto tiene `is_shelter = 1`.],
  [*`X% cannot reach any safe zone`*],
    [La red está fragmentada, o una zona segura quedó en un nodo aislado. Quien
     parta de allí se cuenta como sin ruta antes de que empiece la simulación.
     Por encima de un 10% aproximadamente, conviene corregirlo.],
  [`network is in N disconnected pieces`],
    [Normalmente líneas sin dividir, o extremos que no coinciden del todo. Ajuste
     la geometría y vuelva a extraer los vértices.],
  [`links shorter than 1 m`], [División excesiva. Fusiónelos o elimínelos.],
  [`no population field`], [Agregue `T_TOTAL` a las manzanas censales.],
)

== Un ejemplo trabajado con el cual comparar

`data/Chimbote_Zona1` es un área completa y funcional, y además realista.
`check_inputs.py` informa cuatro advertencias sobre ella, entre ellas que el
19,8% de sus puntos de partida no puede llegar a una zona segura. Compare su
propia carpeta contra esa, y no contra un conjunto de datos perfecto imaginario.

// ======================================================== PARTE V: EL MODELO ==

= Cómo funciona el modelo <part-model>

Esta parte explica qué ocurre dentro de una corrida. No la necesita para usar
GTEM, pero sí para defender un resultado.

== La secuencia de una corrida

+ *Las rutas se calculan una sola vez.* Una única búsqueda de camino más corto,
  sembrada simultáneamente desde todas las zonas seguras, da a cada intersección
  el siguiente paso hacia la más cercana. El resultado queda en caché, de modo
  que las corridas posteriores sobre la misma red son instantáneas.
+ *Se ubica a las personas.* Cada persona se coloca en un punto al azar dentro
  de una manzana censal, elegida en proporción a la población de esa manzana, y
  se asocia a la intersección utilizable más cercana.
+ *Cada persona espera.* Se sortea un retardo de salida (ver más abajo).
+ *Cada persona camina* su ruta, un paso por cada intervalo de tiempo, a una
  velocidad determinada por su grupo de edad y por cuán aglomerada esté la
  calle.
+ *La corrida se detiene* en la hora de llegada del tsunami, o antes si todas
  las personas ya tienen un desenlace.
+ *Cada persona se clasifica* como evacuada, sorprendida en tránsito o sin ruta.
+ *Se escriben las figuras, las tablas y el informe.*

== Velocidad de caminata

Cada grupo de edad tiene una velocidad de flujo libre, es decir, la velocidad
con la calle para sí solo:

#table(
  columns: (auto, auto, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Grupo*], [*Factor*], [*Velocidad de flujo libre*]),
  [Adultos], [1,00], [1,33 m/s],
  [Niños], [0,80], [1,06 m/s],
  [Adultos mayores], [0,70], [0,93 m/s],
)

A medida que una calle se aglomera, la velocidad cae. Por debajo de 0,3 personas
por metro cuadrado todos se mueven libremente. Por encima de 3,0 personas por
metro cuadrado el movimiento se reduce a un arrastre de 0,2 m/s. Entre ambas
densidades la velocidad cae de forma lineal.

La relación se escala con la velocidad de flujo libre de cada grupo, de modo que
el orden entre grupos se mantiene bajo congestión.

#block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
  *Fuente de la relación densidad–velocidad*

  Mas, E., Suppasri, A., Imamura, F. & Koshimura, S. (2015). Agent-based
  Simulation of the 2011 Great East Japan Earthquake/Tsunami Evacuation: An
  Integrated Model of Tsunami Inundation and Evacuation. _Journal of Natural
  Disaster Science_, 34, 41.

  Las seis constantes son configurables, no están fijadas en el código.
]

== Tiempos de salida

Nadie empieza a moverse en el instante del sismo. Cada persona espera un tiempo
aleatorio tomado de una distribución de Rayleigh cuyo *promedio* es
`departure_mean`. La distribución es asimétrica hacia la derecha: la mayoría
sale antes del promedio, y una cola sale mucho más tarde.

#warn("Este es el supuesto al que los resultados son más sensibles")[
  La forma de la curva de salida es una decisión de modelamiento, no una
  observación de su ciudad. Si usted dispone de datos de encuesta sobre con qué
  rapidez salió realmente la gente durante un simulacro o un evento real, es lo
  más valioso que puede aportar al modelo.
]

== Ruteo

Las rutas se calculan *antes* de la simulación y nunca cambian.

Se supone que toda persona conoce la red vial completa y camina por la ruta más
corta hacia la *zona segura más cercana en distancia*, no la menos concurrida ni
la más rápida bajo congestión.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Consecuencia*], [*Qué implica para sus resultados*]),
  [Nadie cambia de ruta],
    [Quien camina hacia un atasco sigue caminando hacia él. La congestión queda
     algo sobreestimada en el cuello de botella y subestimada en las
     alternativas hacia las que la gente real se desviaría.],
  [Conocimiento perfecto],
    [Las personas reales toman rutas familiares, siguen a la multitud, se
     equivocan de dirección y recogen a su familia primero. Por lo tanto, la
     evacuación de GTEM es *más eficiente que la realidad*. Considere los tiempos
     de despeje como el mejor caso posible.],
  [La más cercana, no la menos concurrida],
    [La demanda se concentra. Una zona segura puede recibir miles de personas
     mientras otra no recibe a nadie.],
)

== Cierre de la corrida y recuento de resultados

La corrida termina con lo que ocurra primero: que todas las personas tengan un
desenlace, o la hora de llegada del tsunami.

Cada persona termina exactamente en uno de tres estados, y GTEM verifica
mientras corre que los tres sumen la cantidad de personas simuladas. Si alguna
vez no cuadraran, la corrida se detendría con un error en lugar de informar una
cifra que deja gente fuera del recuento.

== Qué no modela GTEM

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*No modelado*], [*Consecuencia*]),
  [Vehículos y bicicletas],
    [En una ciudad donde mucha gente conduciría, la congestión resulta
     optimista.],
  [Capacidad de las zonas seguras],
    [Un sitio se cuenta como seguro sin importar cuántas personas lleguen.
     Contraste usted mismo la figura de demanda con la capacidad real.],
  [Inundación],
    [El tsunami es una sola cifra que usted entrega. GTEM no simula la ola, ni
     su extensión, ni su profundidad.],
  [Discapacidad y movilidad reducida],
    [Solo existen tres grupos de edad. Una ciudad con una gran población
     dependiente de cuidados no queda bien representada.],
  [Hogares y conducta grupal],
    [Todos evacuan solos. Nadie espera ni recoge a nadie.],
  [Hora del día],
    [La población es una estimación nocturna, con todos en casa. No se
     representan colegios, lugares de trabajo ni playas.],
  [Edificios, escombros y lesiones],
    [Nada obstruye el movimiento salvo otras personas.],
)

== El estado de la validación

#warn("GTEM no está validado, y el único referente disponible indica que es optimista")[
  Todo lo anterior describe lo que GTEM *calcula*. Si eso coincide con una
  evacuación real es una pregunta distinta y más difícil.

  GTEM desciende de TUNAMI-EVAC1 (Mas, 2012), que *sí* fue validado contra la
  evacuación de Arahama, Sendai, en 2011: cerca del *90% de 2.271 personas se
  salvaron*, y 520 se refugiaron en el edificio de evacuación. Bajo supuestos
  equiparados, el modelo ancestro da *81,5%* y GTEM *83,4%*: cercanos entre sí y
  ambos por debajo de la cifra observada.

  Eso es un punto de partida, no una validación: un escenario, una semilla, una
  cifra agregada. La comparación además es muy sensible al supuesto de salida:
  la misma corrida de GTEM con una salida media 26 minutos más temprana evacua
  al *100%*. Todo esto se detalla en `validation/README.md`.

  Hasta que exista una validación real: use GTEM para comparar alternativas,
  declare los supuestos, y señale en todo informe que el modelo no está
  validado.
]

// ==================================================== PARTE VI: REFERENCIA ====

= Referencia <part-reference>

== Escribir el informe en español <sec-idioma>

Las figuras y ambos informes PDF pueden producirse en español. Fíjelo en el
archivo de configuración:

```
language = es
```

o indíquelo en la línea de comandos, lo que resulta cómodo cuando quiere el
mismo escenario en los dos idiomas:

```bash
python main.py --config mi_corrida.txt --language es
```

`batch_main.py` acepta la misma opción.

#table(
  columns: (1fr, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Se traduce*], [*Siempre en inglés*]),
  [Títulos de figuras, rótulos de ejes y leyendas; todos los encabezados, tablas
   y textos de los informes PDF individual y de lote.],
  [Los nombres de los parámetros de configuración, los encabezados de columna de
   los CSV, los nombres de los archivos de salida, y los valores listados en la
   tabla de configuración del informe.],
)

#tip("Por qué las tablas de datos quedan en inglés")[
  Para que dos corridas puedan compararse columna por columna sin importar en
  qué idioma se escribieron sus informes, y para que un script escrito sobre sus
  resultados siga funcionando cuando un colega ejecute el modelo en el otro
  idioma. El informe en español lo señala en la página donde importa.
]

Dos partes de un informe en español siguen en inglés: las advertencias que emite
el motor de simulación y la salida de la consola. El informe lo indica donde
aparecen las advertencias, para que el lector no quede con la duda.

Para agregar otro idioma, copie la tabla `EN` de `src/text_strings.py`, traduzca
los valores y regístrela en `TABLES`. Las pruebas automáticas verifican que
todos los idiomas tengan las mismas claves y los mismos `{marcadores}` que el
inglés.

== Referencia de comandos

#term("transcripts/main_help.txt", caption: [`python main.py --help`])

#term("transcripts/batch_help.txt", caption: [`python batch_main.py --help`])

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Comando*], [*Propósito*]),
  [`python check_environment.py`], [¿Puede este equipo ejecutar GTEM?],
  [`python check_inputs.py <zona>`], [¿Son utilizables los datos de esta área?],
  [`python main.py --config <archivo>`], [Ejecutar una simulación.],
  [`python main.py --config <archivo> --language es`],
    [La misma corrida, con el informe en español.],
  [`python batch_main.py --input <csv>`], [Ejecutar muchas, con estadísticas.],
  [`python -m pytest tests/ -m "not engine"`],
    [Autoprueba rápida, alrededor de un minuto.],
  [`python -m pytest tests/`], [Autoprueba completa, alrededor de media hora.],
)

== Códigos de salida

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Código*], [*Significado*]),
  [`0`], [Terminó; se escribieron todas las salidas.],
  [`1`], [La corrida falló. Queda una marca `FAILED.txt` en la carpeta de
     salida.],
  [`2`], [La configuración o los datos de entrada son inválidos. No se ejecutó
     nada.],
)

== Estructura de carpetas

#term("transcripts/folder_tree.txt",
  caption: [El primer nivel de una carpeta de GTEM.])

== Solución de problemas

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Síntoma*], [*Causa y solución*]),
  [`JVM DLL not found`, pero el archivo sí existe],
    [Python y el motor Java de NetLogo están compilados para procesadores
     distintos. En una Mac con Apple Silicon esto suele significar una versión
     Intel de Python, con frecuencia Anaconda en `/opt/anaconda3`, ejecutándose
     bajo Rosetta. Verifique con
     `python -c "import platform; print(platform.machine())"`: debe imprimir
     `arm64`. Si no, vuelva a crear el entorno con Miniforge.
     `check_environment.py` ahora detecta esto antes de ejecutar nada.],
  [`No NetLogo installation was found`],
    [NetLogo no está instalado o está en otra ubicación. Instale la versión
     7.0.4, o defina `NETLOGO_HOME` apuntando a su carpeta. El error enumera los
     lugares donde GTEM buscó.],
  [Se informa que falta un paquete],
    [No ha activado el entorno. Ejecute `conda activate gtem` en esta terminal.],
  [`Zone folder not found`],
    [El parámetro `zone` no coincide con ninguna carpeta dentro de `data/`. Las
     mayúsculas importan.],
  [`uses a geographic (lat/lon) CRS`],
    [Reproyecte todas las capas a un SRC métrico, como UTM.],
  [`is out of range`],
    [El mensaje nombra el parámetro y sus valores aceptables. No se ejecutó
     nada.],
  [La corrida parece colgarse en macOS o Linux],
    [No debería ocurrir en esta versión, que inicia el motor de Java en modo sin
     interfaz gráfica. Si ocurre, informe el problema e incluya la versión de su
     sistema operativo.],
  [Dos corridas idénticas dan resultados distintos],
    [Verifique que `seed` no sea `0`. Una semilla `0` sortea deliberadamente una
     semilla nueva cada vez, y la registra en los resultados.],
  [Errores que mencionan rutas de archivo muy largas en Windows],
    [Mueva la carpeta de GTEM a una ruta corta, como `C:\GTEM`.],
)

== Glosario

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Término*], [*Significado*]),
  [Agente], [Una persona simulada.],
  [Sorprendido en tránsito], [Seguía caminando cuando llegó la ola.],
  [Coeficiente de variación],
    [La dispersión de un conjunto de resultados dividida por su promedio, en
     porcentaje. Sirve para juzgar si se ejecutaron suficientes réplicas.],
  [SRC], [Sistema de referencia de coordenadas. GTEM exige uno proyectado y
     métrico.],
  [ETA], [Hora estimada de llegada del tsunami, en minutos.],
  [Velocidad de flujo libre], [Velocidad de caminata con la calle para sí solo.],
  [Réplica], [Una corrida del mismo escenario con otra semilla aleatoria.],
  [Zona segura],
    [Un punto marcado con `is_shelter = 1`, donde las personas se cuentan como a
     salvo.],
  [Semilla],
    [El número que fija los sorteos aleatorios y hace repetible una corrida.],
  [Sin ruta], [No hay camino a ninguna zona segura desde el punto de partida.],
  [Intervalo de tiempo (`dt`)],
    [Segundos de tiempo simulado que avanzan en cada paso.],
)

== Licencia, cita y créditos

GTEM se publica bajo la licencia MIT. Los datos de las áreas de estudio que se
entregan con él se publican para libre redistribución junto con el software.

*Autores.* Erick Mas (IRIDeS, Universidad de Tohoku, Japón), Luis Moya
(Pontificia Universidad Católica del Perú), Jheyder Perez (Pontificia
Universidad Católica de Chile).

GTEM deriva de TUNAMI-EVAC
(#link("https://github.com/erick2307/TUNAMI-EVAC")[github.com/erick2307/TUNAMI-EVAC]).
Financiado por la Coalition for Disaster Resilient Infrastructure a través del
Programa de Becas CDRI 2025–2026. Construido sobre NetLogo (Wilensky, 1999).

*Si usa GTEM,* por favor cite tanto el software —ver `CITATION.cff`— como la
fuente de la relación densidad–velocidad, Mas et al. (2015).

== Lecturas adicionales dentro de la carpeta de GTEM

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Documento*], [*Contenido*]),
  [`docs/LIMITATIONS.md`],
    [La declaración completa de lo que GTEM puede y no puede responder. Léala
     antes de presentar resultados.],
  [`docs/PREPARING_YOUR_CITY.md`],
    [El esquema de datos de entrada, en formato de referencia.],
  [`docs/VERIFICATION.md`],
    [Evidencia de que el modelo calcula lo que dice calcular.],
  [`docs/ROADMAP.md`], [Brechas conocidas y lo que está previsto.],
  [`validation/README.md`],
    [Por qué GTEM aún no está validado, y qué haría falta para lograrlo.],
  [`CHANGELOG.md`], [Historial de versiones.],
)

#tip("Los documentos complementarios están en inglés")[
  Este manual es la referencia en español. Los archivos enumerados arriba solo
  existen en inglés por ahora.
]

// ================================================= APÉNDICE: CAPTURAS =====

#pagebreak()

#heading(level: 1, numbering: none)[Apéndice — capturas de pantalla pendientes]

Este manual está escrito de modo que sea completo y utilizable *sin* capturas de
pantalla. Aun así, nueve lugares quedarían más claros con una, y cada uno está
señalado en el texto con un recuadro naranja de línea discontinua.

Para agregar una: tome la captura, guárdela en `docs/manual/figures/` con el
nombre de archivo indicado abajo, y en `manual_es.typ` reemplace todo el bloque
`#todo-shot(...)` por

```
#figure(image("figures/S1.png", width: 90%),
        caption: [NetLogo 7.0.4 en la página de descargas.])
```

Después vuelva a compilar:

```bash
typst compile docs/manual/manual_es.typ docs/manual/GTEM_Manual_ES.pdf
```

Las capturas se comparten con la edición en inglés del manual: basta tomarlas
una vez.

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*N.º*], [*Archivo*], [*Qué capturar*]),
  [S1], [`S1.png`],
    [La página de descargas de NetLogo con la versión 7.0.4 visible. Los
     lectores suelen instalar la versión más reciente.],
  [S2], [`S2.png`],
    [La carpeta de GTEM descomprimida en el Explorador de Windows o en el Finder
     de macOS, mostrando `main.py`, `data`, `examples`, `docs` y `src` en el
     primer nivel.],
  [S3], [`S3.png`],
    [Un Miniforge Prompt justo después de `conda activate gtem`, con el prefijo
     `(gtem)` al inicio de la línea.],
  [S4], [`S4.png`],
    [La carpeta `Outputs/Synthetic_Corridor/1/` mostrando los 14 archivos de
     salida.],
  [S5], [`S5.png`],
    [Un archivo de configuración abierto en un editor de texto simple (Bloc de
     notas, TextEdit o VS Code), para que el lector vea la estructura
     `parámetro = valor`.],
  [S6], [`S6.png`],
    [El cuadro de diálogo *Guardar objetos como…* de QGIS con el selector de SRC
     mostrando una zona UTM. La reproyección es el error de preparación más
     común.],
  [S7], [`S7.png`],
    [*Vectorial ▸ Herramientas de geometría ▸ Extraer vértices* de QGIS, usado
     para derivar los puntos de intersección de la red vial.],
  [S8], [`S8.png`],
    [La calculadora de campos de QGIS creando el campo `cost` a partir de
     `$length`.],
  [S9], [`S9.png`],
    [La tabla de atributos de las intersecciones con la columna `is_shelter`,
     mostrando valores `0` y `1`.],
)

#v(0.6em)

Tome cada captura a un tamaño de lectura cómodo, sobre fondo claro si es
posible, y recorte al cuadro de diálogo o ventana en cuestión en lugar de
capturar todo el escritorio.
