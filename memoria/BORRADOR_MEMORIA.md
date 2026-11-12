# BORRADOR DE MEMORIA — Proyecto Intermodular

> **Cómo usar este borrador**
>
> - Es una **base**, no el documento final. Cópialo en la **plantilla oficial del campus** y **reescríbelo con tus palabras**, añadiendo tu experiencia real (problemas que tuviste, decisiones que tomaste, tu mejora propia).
> - Lo que está entre `[CORCHETES]` lo tienes que completar tú.
> - Formato obligatorio: Calibri 11 o Times New Roman 12 · interlineado 1,5 · justificado · márgenes 2 cm (sup., inf., dcho.) y 3 cm (izq.) · número de página abajo a la derecha · **toda figura y tabla con leyenda** · entrega en PDF.
> - Extensión: **15–20 páginas sin anexos**. Este borrador ocupa unas 15–17 páginas en ese formato con las figuras.
> - Usa los estilos «Título 1 / Título 2» de Word o Google Docs para que el índice se genere solo.

---

## 1. PORTADA

(Usar la de la plantilla oficial)

- **Título:** NetPanel: panel web de monitorización de la disponibilidad de equipos de red
- **Alumno/a:** [Tu nombre y apellidos]
- **Ciclo:** [Nombre del ciclo formativo]
- **Curso académico:** 2026-2027
- **Tutor/a:** [Nombre del tutor/a]
- **Modalidad:** Proyecto de investigación experimental

---

## 2. RESUMEN

Las pequeñas y medianas organizaciones dependen cada vez más de su red informática, pero a menudo no disponen de ninguna herramienta que les avise cuando un servidor, un router o un equipo deja de funcionar: la incidencia se descubre cuando un usuario se queja. Este proyecto diseña, desarrolla y prueba **NetPanel**, una aplicación web ligera que comprueba de forma periódica si los equipos de una red responden, mediante mensajes ICMP (*ping*) o conexiones TCP a un puerto de servicio, y muestra en un panel su estado, su dirección IP, su latencia y su historial de disponibilidad.

La aplicación se ha desarrollado en Python con el microframework Flask y una base de datos SQLite. Un proceso en segundo plano realiza las comprobaciones en paralelo, registra cada resultado, detecta las caídas y recuperaciones y puede enviar avisos por Telegram. Se ha validado con 22 pruebas automáticas, en un laboratorio virtual con Docker en el que se simulan averías y en una red doméstica real. Por último, se propone su implantación en un hogar y en una pyme, aplicando medidas de seguridad como HTTPS, control de acceso y el principio de mínimo privilegio. El resultado es una herramienta funcional, gratuita y fácil de entender y adaptar, que reduce el tiempo de detección de una caída a menos de un minuto.

**Palabras clave:** monitorización de red, disponibilidad, ICMP, Python, Flask.

---

## 3. ÍNDICE

(Generar automáticamente)

---

## 4. JUSTIFICACIÓN DEL PROYECTO

En cualquier organización actual, desde una oficina de cinco personas hasta un instituto, el trabajo diario depende de que una serie de equipos estén disponibles: el router que da salida a Internet, el servidor de ficheros, el controlador de dominio, las impresoras o los propios puestos de trabajo. Cuando uno de ellos falla, la actividad se detiene parcial o totalmente.

El problema no es solo la avería, sino **el tiempo que se tarda en detectarla**. Sin un sistema de monitorización, el departamento de sistemas (o la persona que hace sus funciones en una pyme) se entera de la caída cuando un usuario la sufre y la comunica. Por ejemplo, si el servidor de copias de seguridad se apaga un viernes por la noche, es posible que nadie lo note hasta que se necesite restaurar un archivo, y entonces se descubre que las copias llevan días sin hacerse. Además, sin un registro histórico no es posible saber desde cuándo falla un equipo, cada cuánto lo hace o si un proveedor cumple la disponibilidad que ha contratado.

[Añade aquí un dato contrastado con su fuente sobre el coste de las paradas informáticas o la falta de monitorización en pymes. Por ejemplo, busca informes de INCIBE, del Observatorio Nacional de Tecnología y Sociedad (ONTSI) o de fabricantes reconocidos, y cítalo.]

Existen herramientas profesionales que resuelven este problema, como Zabbix, Nagios o PRTG. Sin embargo, su instalación, configuración y aprendizaje son costosos para una organización pequeña sin personal especializado, y algunas son de pago. Hay, por tanto, un hueco para una herramienta **sencilla, gratuita, en español y fácil de entender**, que responda a la pregunta básica «¿qué equipos de mi red están funcionando ahora mismo y cuáles han fallado?».

Desde el punto de vista formativo, el proyecto es especialmente adecuado porque **integra contenidos de varios módulos del ciclo**: redes (direccionamiento IP, protocolos ICMP y TCP), sistemas operativos (servicios en Linux, usuarios y permisos), programación (Python), bases de datos (modelo entidad-relación y SQL), lenguajes de marcas y desarrollo web (HTML, CSS, JavaScript, JSON) y seguridad informática. [Ajusta la lista con los nombres exactos de los módulos de tu ciclo.]

Por último, existe una motivación personal: [explica por qué te interesa: por ejemplo, tu interés por la administración de sistemas, alguna experiencia en prácticas o en casa con equipos que fallaban, o que quieres orientar tu carrera a un puesto de técnico de sistemas o redes].

---

## 5. INTRODUCCIÓN

### 5.1. La monitorización de redes

La monitorización de red es el uso de un sistema que vigila de forma continua los componentes de una red para detectar componentes lentos o que fallan y avisar al administrador (Kurose y Ross, 2021). Se pueden distinguir varios niveles:

- **Disponibilidad**: ¿el equipo o servicio responde? Es el nivel más básico y el que aborda este proyecto.
- **Rendimiento**: latencia, pérdida de paquetes, uso de ancho de banda, CPU o memoria.
- **Registros y eventos**: análisis de *logs* para detectar errores o incidentes de seguridad.

Existen dos enfoques generales. En la **monitorización activa** (o *sintética*) el sistema de monitorización envía peticiones a los equipos y analiza las respuestas, sin instalar nada en ellos. En la **monitorización pasiva** o basada en agentes, cada equipo ejecuta un programa que informa de su estado, o se consultan sus contadores mediante el protocolo SNMP. NetPanel sigue el enfoque activo, que tiene la ventaja de no requerir ninguna instalación en los equipos vigilados.

### 5.2. Protocolos utilizados para comprobar un equipo

**ICMP (Internet Control Message Protocol)**, definido en el RFC 792 (Postel, 1981), es un protocolo de control que viaja encapsulado en IP y pertenece a la capa de red (capa 3 del modelo OSI). El comando `ping` envía un mensaje ICMP *echo request* (tipo 8) y espera un *echo reply* (tipo 0). Si llega la respuesta, el equipo es alcanzable, y el tiempo transcurrido es la **latencia** o tiempo de ida y vuelta (RTT, *Round Trip Time*). Su principal limitación es que muchos cortafuegos bloquean ICMP; por ejemplo, el cortafuegos de Windows lo bloquea por defecto en sus perfiles estándar.

**TCP (Transmission Control Protocol)**, especificado actualmente en el RFC 9293 (Eddy, 2022), es un protocolo de transporte (capa 4) orientado a conexión. Toda conexión comienza con el **saludo en tres pasos**: el cliente envía un segmento SYN, el servidor responde SYN-ACK si el puerto está abierto y el cliente confirma con ACK. Intentar esta conexión sobre un puerto concreto (80 para HTTP, 443 para HTTPS, 445 para compartición de archivos SMB, 3389 para escritorio remoto, etc.) permite comprobar no solo que la máquina está encendida, sino que **un servicio concreto está funcionando**.

[Figura 1. Comparación entre la comprobación por ICMP y por TCP en el modelo OSI. — puedes usar la tabla «¿Ping o TCP?» de la web del proyecto.]

### 5.3. Disponibilidad y acuerdos de nivel de servicio

La **disponibilidad** (*availability* o *uptime*) es el porcentaje de tiempo en que un sistema está operativo. Se suele expresar en «nueves»: una disponibilidad del 99 % permite unas 7,2 horas de parada al mes; un 99,9 %, unos 43 minutos; y un 99,99 %, unos 4,3 minutos. Estos valores se utilizan en los **acuerdos de nivel de servicio** (SLA) entre proveedores y clientes. Medir la disponibilidad propia permite comprobar si un proveedor (por ejemplo, de conexión a Internet) cumple lo contratado.

**Tabla 1. Tiempo de parada máximo según el nivel de disponibilidad.**

| Disponibilidad | Parada máxima al mes | Parada máxima al año |
|---|---|---|
| 99 % | 7,2 horas | 3,65 días |
| 99,9 % | 43,2 minutos | 8,76 horas |
| 99,99 % | 4,3 minutos | 52,6 minutos |

### 5.4. Herramientas existentes

**Tabla 2. Comparativa de herramientas de monitorización.**

| Herramienta | Licencia | Puntos fuertes | Limitaciones para una pyme pequeña |
|---|---|---|---|
| Zabbix | Libre (AGPL) | Muy completa: agentes, SNMP, plantillas, gráficas, escalado de alertas | Instalación y curva de aprendizaje elevadas (servidor, base de datos, frontend) |
| Nagios Core | Libre (GPL) | Estándar histórico, gran cantidad de *plugins* | Configuración mediante ficheros de texto, interfaz anticuada |
| PRTG | Comercial | Muy sencilla, autodescubrimiento | De pago a partir de 100 sensores; servidor solo en Windows |
| Uptime Kuma | Libre (MIT) | Interfaz moderna y sencilla | Orientada a servicios web más que a inventario de red |
| **NetPanel** | Libre (MIT) | Ligera, en español, código comprensible y adaptable | Sin SNMP ni agentes |

[Fuente: documentación oficial de cada herramienta. Comprueba las condiciones de licencia actuales en sus webs antes de entregar.]

### 5.5. Tecnologías del proyecto

- **Python** es un lenguaje interpretado y multiplataforma, muy usado en administración de sistemas y automatización por su sencillez y su amplia biblioteca estándar, que incluye módulos para ejecutar comandos (`subprocess`), trabajar con *sockets* (`socket`), direcciones IP (`ipaddress`), hilos (`threading`) y bases de datos SQLite (`sqlite3`) (Python Software Foundation, 2025).
- **Flask** es un *microframework* web para Python que proporciona lo esencial (enrutado de URLs, plantillas Jinja2, sesiones) y deja el resto a elección del desarrollador (Grinberg, 2018; Pallets, 2025).
- **SQLite** es un motor de base de datos SQL embebido que almacena toda la base de datos en un único fichero y no necesita un servidor (SQLite, 2025).
- **HTML, CSS y JavaScript** para la interfaz, que se actualiza sin recargar la página mediante peticiones asíncronas (`fetch`) a una API que devuelve JSON (MDN, 2025).

---

## 6. OBJETIVOS

### Objetivo general

Desarrollar una aplicación web que permita conocer en tiempo real si los equipos de una red responden y que registre su historial de disponibilidad.

### Objetivos específicos

1. **Comprobar** periódicamente y de forma automática la disponibilidad de ordenadores, servidores y routers mediante ICMP y TCP.
2. **Mostrar** en un panel web el estado, la dirección IP y la latencia de cada equipo, actualizándose sin recargar la página.
3. **Registrar** el historial de comprobaciones y de caídas para calcular la disponibilidad en distintos periodos.
4. **Avisar** al administrador cuando un equipo cae o se recupera.
5. **Aplicar** medidas de seguridad en el desarrollo y en el despliegue de la aplicación.
6. **Validar** el funcionamiento en un entorno de laboratorio controlado y en una red real, y **proponer** su implantación en un hogar y en una pyme.

---

## 7. DESARROLLO

### 7.1. Metodología y planificación

Se ha seguido un desarrollo **iterativo e incremental**: primero una versión mínima que comprobaba un equipo por consola, y después, en sucesivas iteraciones, el almacenamiento en base de datos, el panel web, el historial, la seguridad, el laboratorio y el despliegue. Cada iteración terminaba con pruebas.

**Tabla 3. Fases del proyecto.** [Ajusta fechas y horas reales.]

| Fase | Tareas | Fechas | Horas |
|---|---|---|---|
| 1. Análisis | Estudio del problema, requisitos, comparativa de herramientas | [ ] | [ ] |
| 2. Formación | Repaso de redes, Python, Flask y SQL | [ ] | [ ] |
| 3. Diseño | Arquitectura, modelo de datos, interfaz | [ ] | [ ] |
| 4. Desarrollo | Comprobador, monitor, web, API, seguridad | [ ] | [ ] |
| 5. Pruebas | Tests automáticos, laboratorio Docker, red doméstica | [ ] | [ ] |
| 6. Despliegue | Servicio systemd, nginx, documentación de uso | [ ] | [ ] |
| 7. Documentación | Memoria, web del proyecto, presentación | [ ] | [ ] |

[Figura 2. Diagrama de Gantt de la planificación. — hazlo en una hoja de cálculo o en GanttProject.]

**Herramientas utilizadas:** Visual Studio Code como editor, Git y GitHub para el control de versiones (el historial de cambios queda como evidencia del trabajo), Docker para el laboratorio, Google Chrome/Firefox para las pruebas de la interfaz y pytest para las pruebas automáticas. Como apoyo se ha utilizado un asistente de inteligencia artificial para generar código base y documentación; todo el contenido ha sido revisado, probado, comprendido y adaptado por el autor. [Ajusta esta frase a cómo lo hayas usado de verdad.]

### 7.2. Requisitos

**Requisitos funcionales:**

- RF1. Dar de alta, modificar y eliminar equipos (nombre, IP o nombre DNS, tipo, puerto opcional, ubicación, descripción).
- RF2. Importar equipos desde un fichero CSV.
- RF3. Comprobar todos los equipos activos cada cierto intervalo configurable.
- RF4. Mostrar un resumen (total, responden, caídos, disponibilidad global) y una tarjeta por equipo.
- RF5. Mostrar para cada equipo su disponibilidad en 24 horas, 7 días y 30 días, una gráfica de latencia y su historial de cambios de estado.
- RF6. Registrar las incidencias (caídas y recuperaciones) y enviar avisos opcionales.
- RF7. Restringir la gestión de equipos a un usuario administrador.

**Requisitos no funcionales:**

- RNF1. Funcionar en Linux y Windows.
- RNF2. Funcionar sin conexión a Internet (sin depender de recursos externos).
- RNF3. Detectar una caída en menos de un minuto con la configuración por defecto.
- RNF4. Interfaz adaptable a móvil (*responsive*).
- RNF5. Seguir buenas prácticas de seguridad (OWASP).

### 7.3. Arquitectura

La aplicación tiene dos componentes que se ejecutan a la vez dentro del mismo proceso de Python y se comunican a través de la base de datos:

- El **monitor**, un hilo en segundo plano que comprueba los equipos y escribe los resultados.
- El **servidor web** (Flask), que atiende las peticiones del navegador, lee de la base de datos y devuelve páginas HTML o datos JSON.

[Figura 3. Arquitectura de NetPanel. — usa el diagrama de la web del proyecto.]

El código se organiza siguiendo el principio de **separación de responsabilidades**:

**Tabla 4. Módulos de la aplicación.**

| Fichero | Responsabilidad |
|---|---|
| `config.py` | Leer la configuración de variables de entorno |
| `db.py` | Definir las tablas y gestionar las conexiones |
| `comprobador.py` | Comprobar un equipo por ICMP o TCP |
| `monitor.py` | Bucle periódico, registro de resultados y avisos |
| `estadisticas.py` | Cálculo de disponibilidad y series para gráficas |
| `seguridad.py` | Inicio de sesión y protección CSRF |
| `rutas.py` | Páginas web y API JSON |
| `templates/`, `static/` | Interfaz (HTML, CSS, JavaScript) |

### 7.4. Modelo de datos

Se utilizan tres tablas relacionadas:

- `equipos`: un registro por equipo, con sus datos y su **estado actual** (para mostrarlo rápidamente).
- `comprobaciones`: un registro por cada comprobación (fecha, si respondió, latencia). Es el **historial**.
- `eventos`: un registro por cada **cambio de estado** (caída o recuperación).

Ambas tablas dependientes tienen una relación 1:N con `equipos`, con claves ajenas y borrado en cascada. Se ha creado un índice sobre `(equipo_id, fecha)` porque es el criterio de casi todas las consultas del historial.

[Figura 4. Diagrama entidad-relación.]

La disponibilidad se calcula directamente en SQL. Como el campo `responde` vale 1 o 0, su media es la proporción de respuestas correctas:

```sql
SELECT AVG(responde) * 100 FROM comprobaciones
WHERE equipo_id = ? AND fecha >= ?;
```

### 7.5. Funcionamiento del monitor

En cada ciclo el monitor:

1. Lee los equipos activos.
2. Los comprueba **en paralelo** mediante un conjunto de hilos (`ThreadPoolExecutor`). Si se comprobasen uno tras otro, 50 equipos caídos con un segundo de espera tardarían 50 segundos; en paralelo, el ciclo dura poco más que la comprobación más lenta. El uso de hilos es eficaz porque la tarea consiste en esperar respuestas de la red.
3. Para cada equipo ejecuta el comando `ping` del sistema (o abre una conexión TCP si tiene puerto configurado), adaptando los parámetros a Linux, Windows o macOS, y extrae la latencia de la salida.
4. Guarda el resultado en el historial.
5. Calcula el nuevo estado: si responde, pasa a «up»; si falla **dos veces seguidas**, pasa a «down». Este umbral evita falsas alarmas por la pérdida puntual de un paquete. Si el estado cambia, se registra un evento y se envía un aviso.
6. Elimina el historial más antiguo que el periodo de retención (30 días por defecto).

[Figura 5. Diagrama de flujo del ciclo de comprobación.]

[Aquí cuenta un problema real que te encontraste y cómo lo resolviste. Por ejemplo: «Durante las pruebas observé que en Windows el ping devolvía éxito aunque el destino fuese inalcanzable; investigando descubrí que…».]

### 7.6. Interfaz de usuario

El panel principal muestra cuatro indicadores de resumen y una tarjeta por equipo con su icono, nombre, IP, método de comprobación, estado, latencia y disponibilidad de las últimas 24 horas. Se puede filtrar por tipo y buscar por nombre o IP. La página se actualiza cada cinco segundos mediante peticiones asíncronas a la API, sin recargarse.

La ficha de cada equipo incluye la disponibilidad en tres periodos, una barra por tramo horario coloreada según la disponibilidad, una gráfica de latencia dibujada en SVG y la tabla de cambios de estado. No se han utilizado librerías externas de gráficos para que la aplicación funcione en redes sin acceso a Internet. La interfaz se adapta al móvil y al modo oscuro del sistema.

[Figuras 6, 7 y 8. Capturas del panel principal, de la ficha de un equipo y de la vista móvil. — están en `docs/img/`.]

### 7.7. Seguridad

**Tabla 5. Medidas de seguridad aplicadas.**

| Riesgo | Medida |
|---|---|
| Robo de contraseñas | Contraseña en variable de entorno, almacenada como *hash* scrypt con sal |
| Inyección de comandos | Validación de la IP o nombre DNS y ejecución de `ping` sin intérprete de comandos |
| Inyección SQL | Consultas parametrizadas en todas las operaciones |
| XSS | Escapado automático en plantillas Jinja2 y función de escape en JavaScript |
| CSRF | Token aleatorio en sesión y en cada formulario |
| Redirección abierta | Solo se permiten redirecciones a rutas internas tras el login |
| Exposición del panel | En producción: HTTPS, acceso solo desde la red de administración, login también para consultar |
| Privilegios excesivos | Servicio con usuario sin privilegios y endurecimiento de systemd |

### 7.8. Pruebas

**Pruebas automáticas.** Se han escrito 22 pruebas con pytest que verifican la validación de direcciones (incluidas entradas maliciosas como `1.1.1.1; rm -rf /`), la regla de cambio de estado, el ping real a la propia máquina, la detección de un puerto cerrado, el registro de eventos, la API, el alta, edición y baja de equipos, que no se puedan añadir equipos sin iniciar sesión y el rechazo de credenciales incorrectas. Todas se superan.

[Figura 9. Resultado de la ejecución de las pruebas automáticas.]

**Laboratorio controlado.** Con Docker Compose se ha creado una red privada `172.30.0.0/24` con seis contenedores que simulan un router, un servidor web nginx, un servidor de ficheros, dos ordenadores y una impresora, además de una dirección sin equipo. Se han realizado los siguientes casos de prueba:

**Tabla 6. Casos de prueba en el laboratorio.** [Rellena con tus resultados reales.]

| Caso | Acción | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| CP1 | Arranque | Todos los equipos existentes «Responde»; el inexistente «Caído» | [ ] |
| CP2 | Detener un PC | Pasa a «Caído» tras 2 ciclos (~20 s) y se registra la incidencia | [ ] |
| CP3 | Arrancar el PC | Pasa a «Responde» y se registra la recuperación | [ ] |
| CP4 | Detener el servidor web (TCP 80) | Pasa a «Caído» | [ ] |
| CP5 | Introducir una IP no válida | El formulario la rechaza | [ ] |
| CP6 | Intentar añadir equipo sin sesión | Redirige al login | [ ] |

[Figura 10. Secuencia de capturas: equipo detenido → caído → arrancado → recuperado.]

**Red real.** La aplicación se ha ejecutado durante [N] días en la red doméstica del autor vigilando [lista de equipos]. [Comenta los resultados: disponibilidad obtenida, alguna caída real detectada, latencias observadas por cable y por Wi-Fi…]

### 7.9. Implantación

**En un hogar.** Se recomienda instalarlo en un equipo siempre encendido de bajo consumo, como una Raspberry Pi; configurar reservas DHCP en el router para que las IPs de los equipos no cambien; incluir una dirección externa (por ejemplo 8.8.8.8) para distinguir una caída de Internet de una caída de la red local; y configurar avisos por Telegram. El panel no debe exponerse a Internet; para consultarlo desde fuera se usaría una VPN.

**En una pyme.** El procedimiento propuesto es: obtener autorización por escrito y el inventario de la red; crear una máquina virtual Linux en la VLAN de administración; ejecutar el script de instalación, que crea un usuario sin privilegios, el entorno de Python, genera claves aleatorias y registra un servicio systemd; instalar nginx como proxy inverso con HTTPS y restringir el acceso por IP; crear un nombre DNS interno; permitir en los cortafuegos ICMP y los puertos necesarios solo desde el servidor de monitorización (en Windows, mediante una directiva de grupo); importar el inventario desde un CSV; y programar copias de seguridad de la base de datos.

[Figura 11. Esquema de despliegue en una pyme.]

**Aspectos legales.** Solo deben monitorizarse redes propias o con autorización expresa. Si los equipos se asocian a personas, el inventario puede contener datos personales sujetos al RGPD y a la LOPDGDD, por lo que el acceso al panel debe limitarse al personal de sistemas.

### 7.10. Presupuesto

**Tabla 7. Presupuesto estimado de implantación en una pyme.** [Ajusta el precio/hora a una referencia real de tu zona y cita la fuente.]

| Concepto | Cantidad | Precio | Total |
|---|---|---|---|
| Software (NetPanel, Linux, nginx) | – | 0 € | 0 € |
| Máquina virtual en servidor existente | 1 | 0 € | 0 € |
| Inventario y análisis de la red | [ ] h | [ ] €/h | [ ] € |
| Instalación y configuración | [ ] h | [ ] €/h | [ ] € |
| Reglas de cortafuegos / GPO | [ ] h | [ ] €/h | [ ] € |
| Formación al personal | [ ] h | [ ] €/h | [ ] € |
| **Total** | | | **[ ] €** |

Alternativa doméstica: Raspberry Pi con fuente y tarjeta, [busca el precio actual] €.

---

## 8. CONCLUSIONES

Se ha desarrollado una aplicación web funcional que cumple el objetivo general: conocer en tiempo real qué equipos de una red responden y guardar su historial de disponibilidad. Revisando los objetivos específicos:

1. **Comprobación periódica por ICMP y TCP:** cumplido. Las comprobaciones se realizan en paralelo y una caída se detecta en menos de un minuto con la configuración por defecto.
2. **Panel con estado, IP y latencia:** cumplido, con actualización automática y diseño adaptable al móvil.
3. **Historial y disponibilidad:** cumplido, con disponibilidad a 24 horas, 7 y 30 días, gráfica de latencia y registro de incidencias.
4. **Avisos:** cumplido mediante Telegram. [Si has añadido correo u otra mejora, menciónalo.]
5. **Seguridad:** cumplido en desarrollo (hash, CSRF, consultas parametrizadas, validación de entradas) y en despliegue (HTTPS, mínimo privilegio).
6. **Validación e implantación:** cumplido con 22 pruebas automáticas, el laboratorio Docker y [N] días en una red real, y con la propuesta de implantación doméstica y empresarial.

**Dificultades encontradas.** [Escribe las tuyas. Ejemplos: las diferencias del comando ping entre sistemas operativos, entender la concurrencia con hilos, el bloqueo de ICMP en Windows, configurar la red de Docker…]

**Aportación personal.** [Describe la mejora que hayas implementado tú y cómo lo hiciste.]

**Aprendizajes.** El proyecto me ha permitido [relaciona lo aprendido con los módulos del ciclo y con tu futuro profesional].

**Limitaciones y líneas futuras.** NetPanel responde a la pregunta «¿está disponible?», pero no mide recursos internos de los equipos. Como mejoras se proponen: descubrimiento automático de los equipos de una subred, consulta de métricas mediante SNMP, dependencias entre equipos para evitar avisos en cascada, varios usuarios con roles, avisos por correo, ventanas de mantenimiento y separar el monitor en un servicio independiente para redes grandes. Para organizaciones con cientos de equipos o necesidades avanzadas, la recomendación profesional sigue siendo una herramienta como Zabbix.

---

## 9. BIBLIOGRAFÍA

(Formato APA 7. Comprueba cada enlace y añade la fecha de consulta.)

- Eddy, W. (Ed.). (2022). *Transmission Control Protocol (TCP)* (RFC 9293). IETF. https://www.rfc-editor.org/rfc/rfc9293
- Grinberg, M. (2018). *Flask web development: Developing web applications with Python* (2.ª ed.). O'Reilly Media.
- Kurose, J. F. y Ross, K. W. (2021). *Computer networking: A top-down approach* (8.ª ed.). Pearson.
- MDN Web Docs. (2025). *Using the Fetch API*. Mozilla. https://developer.mozilla.org/es/docs/Web/API/Fetch_API/Using_Fetch
- OWASP Foundation. (2021). *OWASP Top 10:2021*. https://owasp.org/Top10/
- Pallets. (2025). *Flask documentation*. https://flask.palletsprojects.com/
- Postel, J. (1981). *Internet Control Message Protocol* (RFC 792). IETF. https://www.rfc-editor.org/rfc/rfc792
- Python Software Foundation. (2025). *Documentación de Python 3*. https://docs.python.org/es/3/
- Rekhter, Y., Moskowitz, B., Karrenberg, D., de Groot, G. J. y Lear, E. (1996). *Address allocation for private internets* (RFC 1918). IETF. https://www.rfc-editor.org/rfc/rfc1918
- SQLite. (2025). *SQLite documentation*. https://www.sqlite.org/docs.html
- Tanenbaum, A. S. y Wetherall, D. J. (2011). *Computer networks* (5.ª ed.). Pearson.
- Wiggins, A. (2017). *The twelve-factor app*. https://12factor.net/es/
- Zabbix SIA. (2025). *Zabbix documentation*. https://www.zabbix.com/documentation/current/
- [Añade la fuente del dato de la justificación y otras que consultes.]

---

## 10. ANEXOS

- **Anexo I.** Manual de instalación y uso (resumen de la web del proyecto, sección «Usar la app»).
- **Anexo II.** Capturas de pantalla adicionales (formulario, login, incidencias, modo oscuro, aviso de Telegram).
- **Anexo III.** Salida completa de las pruebas automáticas.
- **Anexo IV.** Fichero `docker-compose.yml` del laboratorio y CSV de equipos de ejemplo.
- **Anexo V.** Glosario: ICMP, TCP, RTT, latencia, disponibilidad, SLA, proxy inverso, WSGI, CSRF, XSS, hash, VLAN, DHCP, DNS.
- **Anexo VI.** Enlaces: repositorio en GitHub y web del proyecto.
  - Código: https://github.com/melvinfranco99/panel-monitorizacion-equipos
  - Web: https://melvinfranco99.github.io/panel-monitorizacion-equipos/
