<div align="center">

<img src="../img/brand/logo.svg" width="72" alt="Mnema">

# Guía de Mnema

Cómo funciona Mnema, pantalla por pantalla y ajuste por ajuste. Mnema responde preguntas sobre sí misma con este mismo texto.

<sub><a href="en.md">English</a> · <a href="ru.md">Русский</a> · <a href="zh.md">中文</a> · <b>Español</b> · <a href="hi.md">हिन्दी</a> · <a href="pt.md">Português</a> · <a href="fr.md">Français</a> · <a href="de.md">Deutsch</a> · <a href="ja.md">日本語</a></sub>

<sub><a href="../../README.es.md">README</a></sub>

</div>

## Contenido

- [Qué es Mnema](#qué-es-mnema)
- [La memoria está activada o desactivada](#la-memoria-está-activada-o-desactivada)
- [Carpeta de memoria](#carpeta-de-memoria)
- [Carpetas de memoria adicionales](#carpetas-de-memoria-adicionales)
- [Cómo se registra un hecho](#cómo-se-registra-un-hecho)
- [Pestaña Memoria](#pestaña-memoria)
- [Retrato](#retrato)
- [Resumen de 10 Now e índice](#resumen-de-10-now-e-índice)
- [Cómo aprende Mnema](#cómo-aprende-mnema)
- [Fuentes de aprendizaje](#fuentes-de-aprendizaje)
- [Modos de aprendizaje](#modos-de-aprendizaje)
- [Cómo entiende Mnema los textos](#cómo-entiende-mnema-los-textos)
- [Cómo decide Mnema: guardar o preguntar](#cómo-decide-mnema-guardar-o-preguntar)
- [Feed de aprendizaje y pregunta en la conversación](#feed-de-aprendizaje-y-pregunta-en-la-conversación)
- [Chat y modelos](#chat-y-modelos)
- [Sesiones](#sesiones)
- [Cómo responde](#cómo-responde)
- [Qué sabe el modelo en cada mensaje](#qué-sabe-el-modelo-en-cada-mensaje)
- [Archivos y documentos, incluidos los PDF](#archivos-y-documentos-incluidos-los-pdf)
- [Internet](#internet)
- [Más preciso o más económico](#más-preciso-o-más-económico)
- [Preguntas con botones, segunda pasada, cita](#preguntas-con-botones-segunda-pasada-cita)
- [Tareas recurrentes](#tareas-recurrentes)
- [Pistas sobre términos](#pistas-sobre-términos)
- [Consorcio](#consorcio)
- [Acciones con archivos](#acciones-con-archivos)
- [Conversación sin aprendizaje](#conversación-sin-aprendizaje)
- [Voz y reuniones](#voz-y-reuniones)
- [Modelo integrado en el ordenador](#modelo-integrado-en-el-ordenador)
- [Motor: tokens y carga](#motor-tokens-y-carga)
- [Quién ve qué (de las IA)](#quién-ve-qué-de-las-ia)
- [Qué sale de tu ordenador](#qué-sale-de-tu-ordenador)
- [Cifrado de la memoria con contraseña](#cifrado-de-la-memoria-con-contraseña)
- [Historial y reversión](#historial-y-reversión)
- [Conectar otras IA](#conectar-otras-ia)
- [Proxy y VPN](#proxy-y-vpn)
- [Ventana, bandeja, instalación](#ventana-bandeja-instalación)
- [Engranaje, tema, idioma, logros](#engranaje-tema-idioma-logros)
- [Varias memorias](#varias-memorias)
- [Telegram](#telegram)
- [Tarjeta "Memoria" abajo a la izquierda](#tarjeta-memoria-abajo-a-la-izquierda)
- [Lo que Mnema no puede hacer](#lo-que-mnema-no-puede-hacer)

## Qué es Mnema

Mnema es un programa de memoria para cualquier IA. Recuerda quién eres, en qué trabajas, qué decisiones has tomado y cómo te gusta que te hablen, y lo incorpora a la conversación con cualquier modelo: Claude, ChatGPT, Gemini, el modelo integrado en tu ordenador, Cursor y agentes. La memoria es una carpeta de archivos Markdown normales en tu ordenador, y puedes abrirla en cualquier editor (incluido Obsidian) incluso sin Mnema. Mnema no tiene nube ni cuenta. El programa consta de una sola ventana (chat, memoria, ajustes) y un icono en la bandeja del sistema (en macOS, en la barra de menús). Funciona en Windows 10 y 11, macOS 11 o posterior (Apple Silicon e Intel) y Linux (64 bits, Ubuntu 22.04 o posterior y similares). La versión personal es gratuita y de código abierto (licencia AGPL-3.0); la versión para empresas se ofrece por separado.

## La memoria está activada o desactivada

La memoria es el interruptor principal de Mnema: un conmutador en el panel "Memoria", abajo a la izquierda del chat (el mismo que está en Ajustes → Aprendizaje → "Memoria"). Mientras la memoria está desactivada, el punto del engranaje, arriba a la derecha, es amarillo. Una memoria nueva, creada en la primera pantalla, empieza desactivada: el tutorial incluye el paso "¿Activar la memoria?" (por defecto, "Sin memoria"), y si el tutorial no se ha mostrado, la misma pregunta aparece en una ventana aparte. La memoria que existía antes de que apareciera el interruptor sigue activada.

Desactivada, es un chat normal con cualquier IA: el modelo no sabe nada de su dueño, Mnema no memoriza nada (no hay aprendizaje, "recuerda" no guarda nada y la acción "guardar en la memoria" falla), y Claude Code, Claude Desktop y Cursor no reciben la memoria ni pueden escribir en ella. Todo lo demás funciona: cualquier modelo, el consorcio, los documentos y el ahorro de tokens en ellos, internet, las reuniones, los modelos locales y las acciones con archivos en las carpetas de trabajo (la carpeta de la memoria queda cerrada para las acciones). La pestaña "Memoria" muestra la pantalla "Memoria desactivada" con los botones "Activar memoria" y "Ver lo guardado". Los ajustes de aprendizaje y "Qué ve cada IA" aparecen atenuados con la etiqueta "Memoria desactivada" y un botón "Activar"; el botón "Sin aprendizaje" del chat está inactivo, y la barra de estado muestra "Memoria desactivada · chat normal, no se memoriza nada".

## Carpeta de memoria

La memoria está en la carpeta que elegiste la primera vez que abriste Mnema. Dentro hay:

| Carpeta o archivo | Qué contiene |
|---|---|
| 00 Inbox/Inbox.md | hechos sin clasificar |
| 10 Now.md | resumen de hoy: quién eres, proyectos activos, últimos eventos, hechos recientes de los últimos 14 días y estados de más de 30 días pendientes de revisar. Se genera sola y no se edita a mano |
| 20 Projects/<nombre>/_Project.md | centro del proyecto: estado (active, paused, closed), objetivo, fecha de inicio, palabras clave, registro. Los documentos del proyecto están al lado |
| 30 People/<nombre>.md | ficha de una persona |
| 60 Events/AAAA-MM.md | decisiones y cambios de estado por mes, los más nuevos arriba |
| 70 Memory/Profile.md | quién eres |
| 70 Memory/Rules.md | cómo trabajar contigo, una regla por línea con su fecha |
| 70 Memory/Thoughts.md | tus pensamientos e ideas |
| 70 Memory/Cards/<tema>.md | ficha de un tema: un hecho por línea, con palabras clave y etiquetas ocultas en el encabezado |
| 70 Memory/Fact archive/ | hechos reemplazados por otros más recientes. Es el historial; los modelos no lo reciben |
| 70 Memory/Index.md | índice: proyectos, fichas y personas con sus palabras clave. Se genera solo |
| 80 Meetings/ | notas de reuniones, transcripciones y resúmenes |
| 90 System/Journal/<día>.md | registro: qué se ha guardado y quién lo ha hecho, en lenguaje claro |
| 90 System/Recipes/ | recetas para tareas repetitivas |
| 95 Saves/ | copia de un archivo antes de su primera edición del día; se conservan las dos últimas |
| 99 Archive/ | proyectos cerrados junto con sus documentos |
| .mnema/ | archivos internos: accesos de la IA, registro de ediciones, instantáneas para deshacer cambios, tokens, ajustes de aprendizaje, conversaciones |

Los archivos de la memoria se pueden editar a mano. Mnema solo lee esta estructura.

## Carpetas de memoria adicionales

Ajustes → Programa → "Carpetas de memoria adicionales": otras carpetas que las IA ven junto con la memoria principal. Sirve cualquiera: notas, una bóveda de Obsidian, documentos, una carpeta compartida del equipo u otra memoria de Mnema. El botón "Conectar Obsidian" encuentra por sí solo las bóvedas de Obsidian que hay en el ordenador (a partir de los ajustes del propio Obsidian) y las muestra con su número de notas: las que marques pasan a ser memoria adicional, y también puedes indicar la carpeta a mano. Cualquier otra carpeta se añade con el botón "Añadir" (o "Elegir…"), y se quita con "Quitar", que aparece a su lado. La bóveda se lee entera una sola vez en segundo plano y después solo las notas modificadas, así que ni siquiera miles de notas ralentizan las respuestas. Los archivos Markdown y de texto se leen en tu ordenador, y a la pregunta solo se envían los fragmentos pertinentes, dentro del mismo volumen que la memoria (control deslizante "Más preciso ↔ Más económico"). Los temas ocultos para esa IA (#money, #health, #private y sus formas en ruso) también se eliminan de estos archivos. Mnema no escribe nada en estas carpetas ni aprende de ellas.

## Cómo se registra un hecho

Un hecho es una línea con fecha: "- 21.09.2026 · Decidimos lanzar el piloto en noviembre". El estado se escribe con la marca "(estado DD.MM.AAAA)". Un estado nuevo del mismo tema sustituye al anterior en el mismo lugar, el anterior pasa al archivo de hechos y el cambio queda registrado en el feed de eventos. Lo que Mnema aprende por sí misma lleva la palabra "aprendido", para que se vea qué proviene del aprendizaje.

La fecha de un hecho aprendido es el día en que lo dijiste o lo escribiste, no el día en que Mnema lo leyó. Si hoy Mnema lee una conversación de hace un mes, el hecho recibirá la fecha de esa conversación y la decisión aparecerá en los eventos de ese mes. Así, lo antiguo no se hace pasar por novedad.

Mnema no saca a una lista aparte los estados con más de 30 días. El modelo conoce la fecha de cada estado: si la conversación toca un estado de hace más de un mes, indica de qué fecha es y te pregunta si sigue vigente.

## Pestaña Memoria

Memoria → Retrato: arriba está el retrato con contadores de datos; debajo, el "Mapa de memoria": los temas en burbujas a tu alrededor. El tamaño depende del número de datos, el candado marca los temas que no ven todas las IA, y pulsa lo que se ha actualizado en los últimos tres días. El nombre de una burbuja pequeña se ve al pasar el cursor por encima. Bajo el mapa hay tarjetas de temas: "Reglas para la IA", "Proyectos", "Personas a tu alrededor", las secciones del retrato, las fichas de temas (primero las más grandes) y "Eventos y decisiones". En cada tarjeta aparece el número de datos y dos líneas recientes (en proyectos y personas, los primeros nombres). Al hacer clic en una tarjeta o en una burbuja, el tema se abre en una ventana superpuesta: todos los datos, una línea por dato, los más recientes arriba, la fecha a la derecha, búsqueda; al hacer clic en un dato se despliega completo, y en los que Mnema ha aprendido aparece ahí mismo "¿de dónde?"; el lápiz abre el archivo. Las secciones del retrato idénticas (por ejemplo, "Quién soy" abierto y oculto) se muestran como un solo tema.

Corrección: en la frase del mapa, "pulsa" debe ser "palpita" (pulsa lo que se ha actualizado → palpita lo que se ha actualizado en los últimos tres días).

## Retrato

El retrato son 2–3 frases al principio de 70 Memory/Profile.md: quién eres, a qué te dedicas y qué es lo más importante para ti ahora. Es lo primero que recibe cada IA. Mnema genera el retrato por sí misma cuando se han acumulado al menos tres datos sobre ti: a partir de las secciones abiertas del perfil, los proyectos activos y las fichas sin etiquetas ocultas (el dinero, la salud y lo personal no entran en el retrato). Lo redacta el modelo elegido para el aprendizaje y, si no hay modelo, se arma con los propios datos en frases cortas. El retrato se regenera después del aprendizaje: de inmediato si ha cambiado el perfil, y no más de una vez cada 6 horas si solo han cambiado las fichas y los proyectos. Si reescribes el retrato tú mismo, Mnema ya no lo toca. La generación aparece en el registro como "retrato generado" y se puede deshacer desde el historial.

## Resumen de 10 Now e índice

Mnema reconstruye por sí misma 10 Now.md y 70 Memory/Index.md después de cada escritura. En 10 Now encontrarás quién eres, los proyectos activos, los últimos eventos, los datos recientes de los últimos 14 días (máximo 12) y los estados obsoletos. En el índice aparece cada proyecto, ficha y persona con las palabras clave para buscarlos. Editar estos archivos a mano no sirve de nada: la próxima vez que se reconstruyan, tus cambios se perderán.

## Cómo aprende Mnema

Mnema aprende sola, a medida que vives tu día a día. No tienes que rellenar cuestionarios ni formularios. Detecta datos en las fuentes que le has permitido y decide si los guarda directamente o te pregunta antes. El aprendizaje se ejecuta en segundo plano según un temporizador (la frecuencia depende del modo del motor: de 10 minutos a 2 horas) y de inmediato con cada mensaje que escribes en el chat de Mnema. En el primer inicio revisa el historial de los últimos 90 días.

En el primer inicio, Mnema pregunta: "¿Puede Mnema mirar otros programas?". Con "No, solo Mnema", aprende únicamente de las conversaciones contigo y de las correcciones que haces en ellas, y trabaja solo con su propia carpeta de memoria: no lee los chats de Claude Code, las notas, los documentos, Telegram, el navegador ni la extensión. Con "Sí, elegiré cuáles" se abre una lista de lo que se ha encontrado en tu ordenador (chats de Claude Code, carpeta de notas, Documentos, exportación de Telegram, historial del navegador, extensión) con sus rutas; ningún elemento viene marcado y Mnema lee solo lo que marques. El correo y el calendario nunca los activa por su cuenta: para ellos hacen falta una dirección y una contraseña, o un enlace secreto.

Todo esto se puede cambiar en Ajustes → Aprendizaje. En "Qué puede mirar Mnema" está el interruptor principal "Otros programas y navegador": si está desactivado, las tarjetas de las fuentes externas aparecen bloqueadas con un candado y no se pueden activar. Más abajo, en "Dónde aprender", cada fuente se activa por separado y en algunas puedes indicar la ruta y las exclusiones.

Mnema nunca lee su propia carpeta de memoria ni sus llamadas internas al modelo.

## Fuentes de aprendizaje

| Fuente | Qué lee |
|---|---|
| Conversaciones en Mnema | tus mensajes en el chat de Mnema, al instante, mientras escribes |
| Conversaciones en Claude Code | tus mensajes del historial de Claude Code (carpeta ~/.claude/projects), solo las líneas nuevas. Se omiten las consultas de servicio de los scripts que empiezan con una etiqueta del tipo "[SERVICIO-NOMBRE]" |
| Exportación de ChatGPT | el archivo conversations.json de la exportación de datos de ChatGPT |
| Tus correcciones | "no, así no", "ya te lo dije", "nunca…" en tus conversaciones con la IA se convierten en reglas para todas las IA |
| Carpeta de notas | líneas nuevas en las notas, por ejemplo en una bóveda de Obsidian. Se excluyen las carpetas de sistema (.obsidian, .trash, .git) |
| Correo | tus correos enviados por IMAP, con las citas recortadas |
| Telegram (conversaciones vía API) | la conversación completa, tus mensajes y los de tus interlocutores, solo en los chats que hayas elegido. Solo lectura; más detalles en la sección "Telegram" |
| Telegram (exportación) | tus propios mensajes de la exportación de Telegram Desktop |
| Calendario | un archivo .ics o un enlace secreto de iCal |
| Documentos | documentos de Word, textos y notas nuevos o modificados en la carpeta elegida (.docx, .txt, .md) |
| Historial del navegador | títulos de las páginas leídas, agrupados por día (Chrome, Edge, Yandex Browser). Por defecto solo observa |

## Modos de aprendizaje

El modo se define para cada fuente:

| Modo | Qué pasa |
|---|---|
| Solo observa | muestra lo que aprendería, pero no escribe nada |
| Pregunta siempre | no escribe nada por su cuenta: en una conversación en Mnema pregunta, y desde otros lugares solo lo muestra |
| Mixto (por defecto) | escribe por su cuenta lo que tiene claro. Lo personal y lo que contradice la memoria, si viene de una conversación en Mnema, lo consulta con una pregunta en la misma conversación; si viene de otros lugares, lo decide por sí misma. Las suposiciones débiles esperan a que se repitan |
| Todo automático | escribe todo; la red de seguridad es el registro de cambios y la posibilidad de revertir |

Si un dato aparece en varias fuentes, se aplica el modo más prudente de todos ellos.

## Cómo entiende Mnema los textos

Mnema puede interpretar el lenguaje cotidiano de distintas maneras (Ajustes → Aprendizaje → "Con qué entiende los textos"):

| Opción | Cómo funciona |
|---|---|
| Por sí misma (por defecto) | el modelo con el que hablas por defecto, sea cual sea el que tengas conectado, en la nube o en tu ordenador; si no hay ninguno, solo las señales explícitas |
| Sin modelo | solo lo explícito: "recuerda …", correcciones, decisiones ("decidí …"), fechas de estados |
| Claude con suscripción | a través de Claude Code instalado, sin herramientas, hooks ni MCP, y la sesión no se guarda |
| Clave propia | Anthropic o un servicio compatible con OpenAI; la clave se guarda en el almacén seguro del sistema (Windows: DPAPI, macOS: Llavero, Linux: almacén de contraseñas, si existe), no en la carpeta de memoria |
| Modelo en el ordenador | integrado u Ollama, nada sale de tu equipo |

Antes de enviar texto a un modelo en la nube, los secretos se sustituyen por marcadores (consulta "Qué sale del ordenador").

## Cómo decide Mnema: guardar o preguntar

- El umbral de confianza por defecto es del 80 %. Si la confianza es del 80 % o más y el dato no es personal, lo guarda por su cuenta. Entre el 60 % y el 80 %, pregunta. Por debajo del 60 %, espera a que el dato aparezca otra vez.
- La repetición aumenta la confianza: dos veces al 60 % dan un 84 %, y el dato se guarda.
- Lo relacionado con dinero, salud o asuntos personales va a una ficha con la etiqueta #money, #health o #private: puedes ocultarla a cualquier IA en la tabla "Qué ve cada IA". Si el tema surge en una conversación dentro de Mnema, antes te preguntará ahí mismo: "Esto es personal, ¿lo recuerdo?".
- Contradicción en la memoria ("vive en Kazán" frente a "es de Ekaterimburgo"): en una conversación dentro de Mnema, te lo pregunta ahí mismo ("Ahora es así", "Era correcto", "Ambas cosas son ciertas"); desde otros lugares, lo nuevo sustituye a lo antiguo, y si la línea antigua decía más, Mnema la reescribe conservando el resto. Lo anterior pasa al archivo de datos.
- "No aprender nunca algo así" añade una frase de exclusión. Revertir un registro aprendido en el historial equivale a un "no": no volverá a aparecer.
- No hay una cola de "te está esperando": Mnema no acumula preguntas. Como máximo hay una pregunta sobre la memoria bajo la conversación al mismo tiempo; la siguiente aparecerá cuando respondas.

## Feed de aprendizaje y pregunta en la conversación

El feed "Aprendo de ti" (engranaje → "Feed") muestra qué ha leído Mnema, qué ha entendido y por qué ha decidido hacerlo así, por ejemplo "confianza del 90 % con un umbral del 80 %, no es personal: lo guardé por mi cuenta" o "esto es dinero: lo guardé en la parte oculta". Si para la memoria hace falta tu palabra, debajo de la conversación aparece una tarjeta "Una aclaración para la memoria" con botones; la respuesta se guarda al instante. Cada línea aprendida tiene "cómo sé esto": la fuente, tus palabras, cuántas veces ha aparecido y por qué se guardó.

## Chat y modelos

Mnema es un chat con cualquier modelo, y todos los modelos son iguales. La elección del modelo está arriba a la izquierda del chat, y el menú tiene dos grupos:

- En la nube: funcionan a través de internet, con una clave (Anthropic, OpenAI, Gemini, OpenRouter, DeepSeek, YandexGPT; Mnema obtiene la lista de modelos del proveedor y, en el caso de YandexGPT, del catálogo de Yandex Cloud AI Studio) o con una suscripción (Claude Code);
- En el ordenador: gratis, sin internet y sin que nada salga al exterior: el modelo integrado (llama.cpp), Ollama y Strata.

DeepSeek se conecta con una clave de platform.deepseek.com. YandexGPT se conecta con la clave de API de una cuenta de servicio de Yandex Cloud AI Studio (rol ai.languageModels.user) y el ID del catálogo en el que se creó: la ventana de conexión tiene dos campos. Modelos de YandexGPT: Alice AI LLM, YandexGPT Pro 5.1, YandexGPT Pro 5, Alice AI LLM Flash, y también DeepSeek V4.1 Flash y Qwen3.6 35B del mismo catálogo. Strata es un programa gratuito independiente para ejecutar modelos grandes (Qwen, DeepSeek) en tu propia tarjeta gráfica (github.com/Niko1221/Strata): instálalo, inicia un modelo con el comando strata launch y Mnema encuentra por sí sola la Strata en ejecución en 127.0.0.1:8080 al arrancar; si usa otra dirección, indícala en la ventana de conexión de Strata.

Los mismos dos grupos están en "Ajustes" → "IA y modelos". El límite de longitud de la respuesta ("Ajustes" → "Motor") es único para todos los modelos, incluido Claude por suscripción.

La memoria y tus reglas se aplican a cada mensaje, y cada modelo recibe solo lo que tiene permitido ver. Cada conversación tiene un título de 1 a 3 palabras. Puedes cambiarlo con el lápiz junto al título, con doble clic sobre el título o desde el menú de la conversación en la lista (Enter para guardar, Escape para cancelar). En una conversación nueva puedes poner el título antes del primer mensaje y se guardará junto con él. Mnema ya no toca lo que renombraste a mano, ni la hora del último cambio ni los tokens gastados. La lista se ordena por fecha o por tokens, y el filtro "IA" muestra las conversaciones con un solo modelo.

El botón "Que Mnema empiece sola" en una conversación vacía: el modelo te saluda y, a partir de la memoria, te propone por dónde empezar. Solo llama recientes a los eventos si lo dice su fecha, y las decisiones de más de un mes te sugiere revisarlas.

## Sesiones

El botón "Nueva sesión" está en la cabecera de la lista, debajo de "Nueva conversación". Una sesión es el conjunto de todas las conversaciones iniciadas después de la última vez que lo pulsaste: "Nueva conversación" abre una conversación dentro de la sesión actual, y "Nueva sesión" empieza un grupo nuevo. En la lista, las conversaciones de una misma sesión se unen con una línea a la izquierda; cada grupo tiene una etiqueta y, a la derecha, el número de conversaciones. La del grupo superior es "Sesión actual" y las de los grupos anteriores, "Sesión · 24 oct" (el día de la última conversación). Al hacer clic en la etiqueta, el grupo se contrae, y Mnema recuerda que lo contrajiste. Justo después de pulsar "Nueva sesión" no aparece ninguna fila vacía: el grupo superior sigue siendo la "Sesión actual" hasta que aparezca la primera conversación en la nueva. Junto a la etiqueta hay un menú ⋮ con "Renombrar" (para ponerle un nombre propio al grupo) y "Eliminar" (borra la sesión junto con sus conversaciones; las fijadas se conservan y lo aprendido queda en la memoria). Las conversaciones iniciadas antes de que existieran las sesiones forman una sesión aparte al final de la lista, y las fijadas aparecen arriba, fuera de los grupos. Al buscar, ordenar por tokens y agrupar por días, la lista es la normal, sin sesiones.

Junto a los botones hay un "?": una animación muestra por qué resulta caro quedarse mucho tiempo en una misma conversación y en qué se diferencian una conversación nueva y una sesión nueva.

Cada conversación envía al modelo solo su propio historial. Por eso, la conversación de una sesión nueva empieza con el contexto limpio: el modelo recibe la memoria y las reglas, pero no el intercambio de las conversaciones anteriores. Una conversación larga envía cada vez más historial con cada respuesta, así que conviene más empezar un tema nuevo con una conversación nueva o una sesión nueva: Mnema ya ha guardado en la memoria lo que hacía falta del pasado.

Cuando una respuesta cuesta el triple que la primera respuesta del mismo modelo en esa conversación (tokens de entrada junto con la caché y la respuesta), debajo aparece la tarjeta "La conversación se ha encarecido" (no aparece con un modelo gratuito en el ordenador): dos barras, la primera y la última respuesta, y cuántas veces más cara es. El botón "Actualizar la memoria y empezar una nueva sesión" primero aprende de toda la conversación de una sola vez y después empieza una sesión nueva con el contexto limpio. Un mensaje que ya se aprendió antes no cuenta como repetido. En una conversación sin aprendizaje, el botón simplemente empieza una sesión nueva. "No volver a mostrar" desactiva el aviso por completo; para recuperarlo, ve al engranaje ("Aviso de conversación cara"). La cruz de la tarjeta la oculta solo en esa conversación.

## Cómo responde

Ajustes → "Cómo responde": nombre, trato (de tú o de usted), longitud de la respuesta (breve, al grano, detallada), género, para las terminaciones (por ejemplo, «seguro» o «segura»), y carácter. Todas las opciones se eligen con tarjetas, y a la derecha aparece "Ejemplo de respuesta": la misma pregunta sobre el piloto, y la respuesta cambia al instante junto con los ajustes; el nombre, mientras lo escribes. Los caracteres (Suave, Profesional, Estricto con verificaciones) son medallas con una escala de verificaciones de una a tres. Más abajo hay conjuntos de reglas y reglas detalladas por grupos.

## Qué sabe el modelo en cada mensaje

Antes de responder, el modelo recibe:
- cómo trabajar contigo: las reglas de la sección "Cómo responde" (carácter, forma de dirigirse a ti, tus propias palabras);
- la memoria que este modelo tiene permitido ver (la cabeza de la memoria y las líneas relacionadas con tu pregunta);
- información sobre cómo está configurada Mnema ahora mismo: dónde aprende, en qué modo está, con qué entiende los textos, cuántas entradas hay en la memoria;
- la fecha de hoy;
- para las preguntas sobre la propia Mnema, las secciones correspondientes de esta base de conocimiento.

El modelo responde como Mnema y, sobre sus capacidades, dice únicamente lo que Mnema sabe hacer. Las capacidades del motor en el que se ejecuta (por ejemplo, las herramientas de Claude Code) no forman parte de Mnema.

## Archivos y documentos, incluidos los PDF

Puedes adjuntar un archivo con el clip que hay debajo del campo de entrada o arrastrándolo a la ventana. Cada archivo puede pesar hasta 25 MB. Mnema lo guarda junto a la conversación y extrae el texto por sí misma, en tu ordenador y sin coste.

| Formato | Qué hace Mnema |
|---|---|
| PDF con capa de texto | extrae el texto página por página (con los números de página) |
| PDF escaneado sin texto | reconoce el texto en tu ordenador (RapidOCR), hasta 40 páginas, y se lo pasa como texto a cualquier modelo. El alfabeto depende del idioma de la interfaz: cirílico (e inglés) para el ruso, latino con diacríticos para los idiomas europeos, chino e inglés para el chino y el japonés. Si no se consigue reconocer nada, el archivo se envía entero al modelo: así solo lo lee Anthropic con clave propia |
| PDF protegido con contraseña | Mnema avisa de que el archivo está protegido con contraseña y te propone quitarla ("Imprimir → Guardar como PDF") |
| Excel (xlsx, xls), CSV, TSV | tabla por hojas, hasta 2000 filas por hoja |
| Word (docx), PowerPoint (pptx), OpenDocument, RTF, HTML | texto; las tablas de Word se convierten en filas, con las celdas separadas por « \| » |
| Archivos de texto y código (txt, md, json, xml, py y otros) | texto tal cual |
| Imágenes (png, jpg, gif, webp) | se las pasa al modelo como imagen (la ven Anthropic, los modelos de proveedores compatibles con OpenAI y Ollama con soporte de imágenes) y, además, reconoce en tu ordenador el texto que haya en la imagen, que recibe cualquier modelo |
| Otros formatos | el modelo recibe solo el nombre del archivo |

El texto completo del documento se guarda junto a la conversación. Salvo en el paso más preciso de "Más preciso ↔ Más económico", el modelo recibe el inicio del documento y los fragmentos que responden a la pregunta actual, y no el archivo entero. En el paso más preciso el texto se inserta completo, pero con un máximo de 60 000 caracteres. Así, con un PDF puedes: hacer un resumen, buscar una respuesta en el texto, extraer datos de identificación y cifras, comparar dos documentos adjuntos o analizar tablas.

Crear y editar archivos, generar PDF, Word y Excel, modificar Word y Excel ya existentes, unir, recortar, rotar y dividir PDF, leer archivos a partir de su ruta: todo eso son acciones con archivos (consulta la sección siguiente). Lo que Mnema no hace con los archivos: no rellena formularios PDF ni ejecuta programas o scripts.

## Internet

El interruptor "Internet" debajo del campo de entrada permite la búsqueda, pero no la activa en cada mensaje. Mnema busca solo cuando sin datos externos recientes no es posible responder con certeza: precios, tipos de cambio, noticias, últimas versiones, horarios, "ahora" y "hoy", y también cuando le pides directamente "busca" o "investiga". En preguntas sobre la propia Mnema, sobre ti, de conocimiento general ("qué es …") y en tareas sobre un texto dado, no va a la red. Un enlace en el mensaje se lee siempre, incluso con el interruptor desactivado. Las páginas de los enlaces y las suscripciones de VPN se abren solo en direcciones de internet: este ordenador, la red doméstica o de oficina y las direcciones de servicio de Mnema están bloqueados.

La búsqueda es gratuita y no requiere claves: Bing y Yahoo mediante la biblioteca ddgs, y después DuckDuckGo, Bing, Yandex y Wikipedia directamente. Los resultados que no coinciden con la mayoría de las palabras clave de la pregunta se descartan. Las páginas se leen y se limpian en tu ordenador, el modelo recibe fragmentos numerados y se refiere a ellos con [1], [2], y las fuentes se muestran debajo de la respuesta. Si internet está desactivado y la pregunta exige claramente datos recientes, Mnema responde con lo que sabe y te propone activar la búsqueda.

## Más preciso o más económico

Ajustes → Motor → Ajuste fino → "Más preciso ↔ Más económico" es un único control deslizante de cinco pasos, situado por defecto en el centro. Más preciso: se contrasta con la pregunta más memoria y más fragmentos del documento, el modelo pide aclaraciones con más frecuencia y la respuesta cuesta más. Más económico: se contrasta menos, y el modelo solo pide aclaraciones cuando no queda otra.

| Paso | Memoria en la consulta | Documento contrastado | Conversación | Pide aclaraciones |
|---|---|---|---|---|
| El más económico | 2 000 caracteres | hasta 3 500 | hasta 8 000 | solo cuando no queda otra |
| Más económico | 3 000 | hasta 5 000 | hasta 11 000 | solo cuando no queda otra |
| Equilibrio (por defecto) | 4 200 | hasta 7 000 | hasta 14 000 | cuando hace falta |
| Más preciso | 8 000 | hasta 12 000 | hasta 20 000 | con más frecuencia |
| Máxima precisión | 16 000 | completo | completa | ante cualquier duda |

En todos los pasos salvo el más preciso, de la memoria se toman el principio y las líneas relacionadas con la pregunta. Los últimos 6 mensajes de la conversación se incluyen completos; los más antiguos se acortan a 400 caracteres. De los documentos y las páginas web se toman los fragmentos pertinentes. Debajo de la respuesta puedes ver cuántos tokens se han ahorrado (estimación: unos 3,5 caracteres por token). Medición con un contrato de 153 000 caracteres: 29 643 tokens de entrada sin ahorro frente a 6 159 con él, y solo la variante con ahorro dio la respuesta correcta.

## Preguntas con botones, segunda pasada, cita

Cuando el modelo necesita una aclaración, hace una sola pregunta en forma de tarjeta: la pregunta en sí, en una línea por qué la hace, y de 2 a 4 opciones en columna, en orden, cada una con una breve explicación de lo que pasará si la eliges. Puedes elegir una opción haciendo clic o con un número del teclado; en la parte inferior de la tarjeta también puedes responder con tus propias palabras. Después de responder, la opción elegida queda marcada con una marca de verificación. En la tarjeta hay un icono de engranaje con tres ajustes: si hacer las preguntas con opciones, si explicar cada opción y si preguntar solo cuando sea necesario. La "Segunda pasada" (en los ajustes) hace que el modelo revise el borrador según tus reglas y tu memoria antes de que lo veas. Puedes citar en tu siguiente mensaje un fragmento seleccionado de la respuesta. El botón "Útil" que aparece debajo de la respuesta indica qué forma de respuesta te resulta adecuada: el modelo toma las respuestas marcadas como modelo de la forma a seguir.

## Tareas recurrentes

En la segunda tarea parecida (o en cada una, o nunca, según lo que configures en los ajustes), Mnema te propone guardar una receta para que la próxima vez no tengas que explicarlo todo de nuevo ni gastar tokens en aclaraciones. La receta —objetivo, datos de entrada, pasos, formato del resultado, comprobaciones y qué no hacer— se guarda en 90 System/Recipes. La siguiente petición parecida se ejecuta sola siguiendo la receta, y debajo de la respuesta verás "según la receta «…»". Mnema determina la similitud en tu ordenador, comparando las raíces de las palabras.

## Pistas sobre términos

Con las "Pistas" activadas (en el menú "+" debajo del campo de entrada), el modelo añade a la respuesta un breve glosario: los términos poco claros y todos los nombres que aparecen en ella, ya sean personas, empresas, productos, servicios o comunidades (por ejemplo, Show HN), excepto tú y las personas de las que hayas hablado tú mismo. Mnema separa el glosario del resto, subraya esas palabras en la respuesta y muestra la explicación al pasar el cursor por encima.

## Consorcio

"Debatir con distintas IA" debajo de cualquier respuesta: primero aparece la ventana "¿Con quién debatir?", con todos los modelos conectados salvo el autor; los mejores vienen marcados de antemano, hasta tres rivales, y el cierre lo hace el primero marcado. El autor de la respuesta la defiende, los rivales buscan dónde es incorrecta, incompleta o dónde hay una opción mejor, y al final llega el veredicto: si la respuesta se sostiene o no y qué hacer. Si hay una sola IA conectada, debaten entre sí sus modelos (por ejemplo, Sonnet con Opus). Es un consorcio normal en formato de debate, que puedes continuar, detener o finalizar.

El botón "Consorcio" bajo el campo de entrada inicia una conversación entre 2 y 4 IA (cualquier modelo conectado, incluido el integrado) de 1 a 20 rondas. Hablan por turnos, se ven entre sí y se dirigen por su nombre; la última hace el resumen: en qué coinciden, en qué no y qué recomiendan. Sobre los mensajes hay una mesa redonda: quién habla, quién es el siguiente y los botones "Pausar", "Continuar", "Finalizar" y "Debatir de nuevo". "Detener" (el botón de enviar mientras se genera una respuesta) corta al orador actual al instante: lo dicho se queda con la marca "interrumpido" y los demás esperan a que pulses "Continuar". Puedes cambiar los participantes y el número de rondas sobre la marcha. Cada participante recibe toda la conversación: los últimos 16 mensajes completos, los anteriores resumidos, los documentos adjuntos por fragmentos según la pregunta, el texto de las imágenes, las propias imágenes y los PDF. Formatos: consejo, debate, lluvia de ideas, equipo rojo y "parrilla" (critican sin piedad una idea, un currículum o un texto; el resumen empieza con una nota "N/10"). Bajo el resumen está "Compartir": una tarjeta en forma de imagen con el resultado. Si escribes durante la conversación, el orador actual se detiene y el debate continúa a partir de tu mensaje; el orador que todavía no ha dicho nada (porque el servicio se ha colgado) se retira de inmediato. El participante cuya clave no sirve o al que se le acabó el saldo lo avisa una sola vez y deja de participar en la conversación; entonces el resumen lo hace otro. Cada participante recibe la memoria según sus permisos de acceso. El consorcio se puede conectar a una conversación que ya está en curso.

La ventana del consorcio es al principio sencilla: a quién invitar al consejo (2–4 IA, el número de la tarjeta indica el turno), el formato de la conversación y una mesa en vivo con los participantes elegidos y el orden de intervención. El botón "Configuración avanzada" abre todo lo demás: rondas, roles, quién hace el resumen, longitud de las intervenciones, verificación de datos y plan de rondas; cada sección tiene su propio "?" con una explicación. "Más simple" devuelve a la vista sencilla.

La verificación de datos (activada por defecto): si un participante se apoya en un hecho, una cifra, una fecha o información reciente, busca por sí mismo en internet (hasta dos consultas por turno) y responde con enlaces [1], [2]. Las fuentes se ven bajo su intervención. En opiniones y consejos no busca. Un turno con búsqueda es más largo: el modelo responde dos veces, antes y después de buscar. Se desactiva en la configuración avanzada: "Buscar en internet".

El engranaje del botón "Consorcio" abre los mismos ajustes:

| Ajuste | Opciones |
|---|---|
| Formato | Consejo: respuesta propia → revisión → mejora → puntos discutidos → respuesta común. Debate: los participantes se reparten alternadamente a favor y en contra, posturas → objeciones → veredicto. Lluvia de ideas: ideas sin críticas → desarrollo de las ideas ajenas → las tres mejores (por qué, primer paso, riesgo). Equipo rojo: ataque a tu plan → cómo cerrar los huecos → lista de riesgos y qué hacer |
| Roles | para cada participante: sin rol, escéptico, pragmático, financiero, abogado, creativo, analista, cliente |
| Quién hace el resumen | el último por turno o un participante elegido: en la última ronda habla en último lugar |
| Intervenciones | breves (hasta 80 palabras, resumen hasta 120), normales (150 y 180), extensas (300 y 350) |

En la parte inferior de la ventana hay un esquema: la mesa con los participantes en orden de intervención, el bando en el debate, una copa para quien hace el resumen y el plan de rondas del formato elegido. El formato, la longitud y los roles se recuerdan para el siguiente consejo.

## Acciones con archivos

El modelo del chat puede trabajar con archivos: leer un archivo (incluidos PDF, Word, Excel y PowerPoint; los escaneos y las imágenes se reconocen en tu ordenador), ver el contenido de una carpeta, buscar archivos por palabras, crear o reescribir un archivo de texto (.md, .txt, .csv, .json, .html), modificar un fragmento de un archivo, crear un documento PDF, Word o Excel a partir de texto con títulos, listas y tablas, y escribir una línea en la memoria. Funciona con cualquier modelo, en la nube o en tu ordenador.

Documentos listos:

| Qué | Cómo |
|---|---|
| Word (.docx) | reemplazo de texto conservando el formato: la frase se encuentra aunque contenga una palabra en negrita o esté dividida en varios fragmentos dentro del archivo; el texto nuevo toma el formato del lugar donde empezaba la frase anterior. También en encabezados, pies de página y notas al pie |
| Excel (.xlsx, .xlsm) | valores y fórmulas en las celdas ("Hoja1!B3 = 1500", "C7 = =SUM(C1:C6)"), reemplazo de texto en las celdas; las demás hojas, los formatos y las fórmulas se conservan. Mnema no edita libros con gráficos, imágenes o tablas dinámicas, porque se perderían al guardar |
| PDF | unir varios archivos, conservar las páginas que necesites en el orden que quieras (también para recortar, eliminar o reordenar), girar páginas 90, 180 o 270 grados, dividir en partes. El archivo original no cambia y el nuevo no sobrescribe uno existente |

De forma predeterminada, Mnema ejecuta la acción de inmediato. Si en Ajustes → Programa → "Acciones con archivos" activas "Pedir permiso para cada acción", debajo de la respuesta aparece una tarjeta "Mnema quiere": qué hará exactamente y con qué archivo, con los botones "Sí", "Sí, en esta conversación" (las acciones del mismo tipo en esta conversación ya no se preguntan) y "No". Después de la acción, en la conversación queda una línea "Archivo creado …" con el botón "Mostrar en la carpeta", y el modelo continúa su respuesta. No se ejecutan programas ni se envía nada a internet.

Dónde se puede: la carpeta de memoria y las carpetas de trabajo que hayas añadido en Ajustes → Programa → "Acciones con archivos"; ahí mismo también se pueden desactivar las acciones por completo. La carpeta de servicio .mnema está cerrada. El modelo lee una nota de la memoria según sus propios permisos: los temas ocultos siguen ocultos. Un documento nunca sobrescribe uno existente: el nuevo recibe un nombre como "informe (2).pdf". Cualquier escritura se puede deshacer: "Memoria" → "Historial", tanto en la memoria como en las carpetas de trabajo. El PDF se genera a través del navegador Edge, Chrome o Chromium sin mostrar su ventana: Edge viene incluido en todos los Windows 10 y 11; en macOS y Linux hace falta uno de ellos.

## Conversación sin aprendizaje

El interruptor "Sin aprendizaje" debajo del campo de entrada hace que esta conversación no enseñe nada a la memoria, desde el primer mensaje. El modelo sigue viendo la memoria, pero no se guarda nada nuevo de la conversación, y la marca "Útil" en ella tampoco enseña nada.

## Voz y reuniones

El micrófono, debajo del campo de entrada, sirve para dictar un comando o grabar una reunión. El comando se graba con el micrófono, se reconoce en tu equipo y se envía como mensaje; el audio se elimina. La grabación de una reunión registra el micrófono y el sonido del equipo en dos canales, por lo que en la transcripción se ve quién habla. También puedes arrastrar al chat un archivo de audio o vídeo (incluidos .mov del iPhone, .mp4, .avi, .3gp, .m4v). Si todavía no hay un modelo de reconocimiento, hay que descargarlo una sola vez (unos 0,5 GB, se necesita conexión a internet); Mnema te avisará. El reconocimiento lo hace faster-whisper en tu equipo (modelo small o medium, si está descargado). También puedes usar Whisper en la nube con una clave de OpenAI: cuesta $0.006 por minuto, unos $0.36 por hora. El modo "Decide la app" (el predeterminado) mide la velocidad del equipo durante el primer minuto y, si no va a terminar en el tiempo que dura la reunión o en 10 minutos, te pregunta si prefieres usar la nube. El audio y Расшифровка.md se quedan en 80 Meetings; al chat llegan la transcripción y un breve resumen, y tus palabras pasan al aprendizaje. En la ventana de grabación de la reunión, arriba a la derecha, está "Configurar", que lleva a Ajustes → Grabaciones de reuniones. Ahí el recorrido de la reunión aparece dibujado en cuatro pasos: Grabación (si se guarda el audio), Transcripción (dónde y con qué precisión), Resumen (qué modelo hace el resumen), Memoria (aprende de tus palabras). Haz clic en un paso y debajo verás su descripción y sus ajustes. Arriba hay configuraciones predefinidas: "Privado" (todo en el equipo, el audio se elimina), "Equilibrado" (la app decide) y "Rápido" (Whisper en la nube). El modelo del resumen también se puede elegir en la propia ventana de grabación.

## Modelo integrado en el ordenador

Mnema lleva integrado un servidor llama.cpp. Puedes elegir entre 13 modelos GGUF de Hugging Face, repartidos en cinco grupos: ligeros (Gemma 3 1B, Qwen2.5 1.5B, Llama 3.2 3B), equilibrados (Gemma 3 4B — la recomendada, Qwen3 4B, Phi-4 mini), inteligentes (Qwen2.5 7B, Llama 3.1 8B, YandexGPT 5 Lite 8B), especiales (Qwen3 4B Thinking, Qwen2.5 Coder 7B) y grandes (Gemma 3 12B, Mistral Small 3.2 24B). De cada uno se indica para qué sirve, su tamaño, la memoria que necesita y cuánto tardará en descargarse con tu conexión. La descarga se puede pausar y reanudar. Los modelos se guardan en ~/.mnema/models. Funciona sin internet y de forma gratuita, pero es menos potente que los modelos en la nube.

Mientras tengas seleccionado un modelo en el ordenador, en la cabecera del chat verás un termómetro: la carga del procesador, la parte que usa el modelo, la memoria y la temperatura, si el sistema la proporciona (en Windows no siempre, en Linux normalmente sí, en macOS no). Si el modelo calienta el ordenador durante un minuto, Mnema le baja la prioridad por su cuenta y te avisa. Hay dos botones: "Reducir carga" y "Detener modelo".

## Motor: tokens y carga

"Ajustes" → "Motor", tres modos:

| Modo | Más preciso ↔ Más económico | Longitud de la respuesta | Núcleos | Contexto | Aprendizaje |
|---|---|---|---|---|---|
| Económico | más económico (3 000 caracteres de memoria) | hasta 1 000 tokens | un cuarto | 4 096 | cada 2 horas |
| Equilibrado (por defecto) | equilibrado (4 200) | 3 000 | la mitad | 8 192 | cada 30 minutos |
| Máximo | máxima precisión (16 000, sin recortes) | 8 000 | todos menos uno | 16 384 | cada 10 minutos |

Ajuste fino: una columna cada uno: "Más preciso ↔ Más económico", la respuesta más larga, el límite mensual, los núcleos del procesador y cuánto mantiene en mente. Si mueves cualquier control deslizante a mano, el modo pasa a "Personalizado". El límite mensual cuenta los tokens de la nube; cuando se agota, las solicitudes a la nube se detienen con un mensaje claro, mientras que el modelo del ordenador sigue funcionando. No se puede limitar la longitud de las respuestas de Claude con suscripción.

Más abajo hay un bloque aparte, "En segundo plano": "No molestar al trabajar" reduce la prioridad del modelo del ordenador, y "Aprendizaje en segundo plano" define la frecuencia con la que Mnema revisa las fuentes de aprendizaje.

## Quién ve qué (de las IA)

Ajustes → Seguridad → "Quién ve qué": una tabla con las IA en columnas y las partes de la memoria en filas, más un bloque de temas privados (Dinero, Salud, Personal), que se recortan incluso de las partes permitidas. Cada cambio se guarda al instante, y el interruptor bajo una columna desactiva por completo esa IA. Por defecto no se oculta nada y cualquier IA puede dejar contenido nuevo en la bandeja de entrada:

| IA | Ve | Puede añadir |
|---|---|---|
| Modelo en el equipo (integrado, Ollama, Strata) | todo | bandeja de entrada |
| Claude, Claude Code | todo | bandeja de entrada, decisiones, proyectos, fichas, personas, reglas |
| ChatGPT | perfil, reglas, proyectos, fichas, decisiones | bandeja de entrada |
| OpenRouter, DeepSeek, YandexGPT | perfil, reglas, proyectos, fichas, decisiones | bandeja de entrada |
| Gemini | perfil, reglas, fichas | bandeja de entrada |
| Cursor | reglas, proyectos | bandeja de entrada |

El modelo en el equipo lo ve todo porque nada sale de tu equipo. Dinero, salud y personal están visibles por defecto para todas las IA que tienen acceso a las Fichas: para ocultar un tema a una IA concreta, pulsa "visible" en su columna y pasará a "oculto".

Una etiqueta de ocultación en un encabezado (por ejemplo, "## Dinero #money") oculta ese encabezado y todo lo que hay debajo. Una etiqueta en el título "# Dinero #money" o en las propiedades del archivo (tags) oculta el archivo entero. También funcionan las etiquetas en ruso (#деньги, #здоровье, #личное), sin distinguir mayúsculas de minúsculas, y las propiedades tal como las escribe Obsidian (tags como lista). Un cambio de estado en una ficha oculta pasa al registro de eventos con la misma etiqueta, así que también queda oculto.

## Qué sale de tu ordenador

Antes de cualquier solicitud a una IA en la nube (chat, consorcio, segunda pasada, títulos de conversaciones, cerebro de aprendizaje, retrato) y antes de cualquier solicitud a los buscadores, los números de tarjeta (con verificación de Luhn), las contraseñas, los PIN y los CVV, las claves de API, los tokens y las claves de VPN, los teléfonos, el pasaporte, el SNILS, el INN y los números de cuenta se sustituyen por etiquetas del tipo [TELÉFONO-1]. La respuesta vuelve con los valores reales ya en tu ordenador. Se activa en "Ajustes" → "Seguridad". El cerebro de aprendizaje que usa una nube ajena recibe la memoria con las mismas reglas que la IA del chat: los temas ocultos no se envían. Cada solicitud al exterior queda como una línea en el registro: cuándo, a quién, para qué (respuesta en el chat, aprendizaje, retrato, título de conversación, búsqueda en internet), cuántos caracteres, cuánta de la memoria disponible salió y qué se ocultó (solo la cantidad, no los valores). Una solicitud que no salió (no hay programa, no hay clave, no hay conexión) no se registra. "Salido en la semana" en la tarjeta "Memoria", abajo a la izquierda, muestra el informe de los últimos 7 días.

## Cifrado de la memoria con contraseña

"Ajustes" → "Seguridad" → "Cifrar la memoria con contraseña", en Windows, macOS y Linux. Lo mismo se te propone en el primer inicio, en el paso "¿Proteger la memoria con contraseña?": por defecto sin contraseña; puedes escribir la tuya o pulsar "Generar una segura". Con una memoria cifrada, la sincronización con Google Drive, Dropbox, tu propia carpeta o la estación envía solo archivos cifrados; una copia con otra contraseña no se acepta y no sobrescribe la tuya. Mnema cifra por sí misma las notas y los archivos de servicio con lo que has dicho y hecho: conversaciones, texto de los adjuntos, el registro y sus instantáneas para deshacer cambios, las huellas del aprendizaje, el informe de lo que ha salido al exterior y el retrato. Sin la contraseña no se pueden leer, ni siquiera copiando la carpeta.

| | |
|---|---|
| Cómo | una clave aleatoria de la memoria (AES-256-GCM) cifra los archivos y la contraseña, mediante scrypt, cifra esa clave; ambas se guardan en .mnema/crypto.json |
| Contraseña | de al menos 8 caracteres y no se puede recuperar: si la olvidas, no hay forma de recuperar la memoria. Puedes cambiarla en cualquier momento y los archivos no se reescriben |
| Recordar en este ordenador | la clave se guarda en el almacén seguro del sistema (Windows: DPAPI; macOS: Llavero; Linux: almacén de contraseñas, si lo hay, y si no, un archivo en la carpeta personal accesible solo para ti): Mnema se abre sin pedirte nada. Si lo desactivas, la contraseña se pide en cada inicio y, hasta que la introduzcas, Mnema no muestra nada ni aprende |
| Qué no se cifra | los archivos binarios (PDF, Word, imágenes, grabaciones de reuniones), porque los abren otros programas; los ajustes que se necesitan antes de la contraseña (idioma, modelos, permisos de acceso de la IA); las carpetas de otros programas (.obsidian y similares) |
| Inconveniente | Obsidian y otros editores no podrán abrir las notas cifradas. Si otro programa guarda una nota en la carpeta, Mnema la cifrará la próxima vez que se abra |
| Fallo a mitad de proceso | los archivos se cifran uno a uno: cada uno se escribe al lado, se comprueba que se lee de vuelta igual y solo entonces sustituye al antiguo. Si apagas el ordenador a mitad, una parte de los archivos quedará sin cifrar, pero todos se podrán leer, y la próxima vez que se abra Mnema terminará de cifrar el resto |
| Claude Code, Cursor (MCP) | reciben la memoria como antes, si Mnema está en ejecución o la contraseña está recordada en este ordenador |

"Quitar el cifrado" (el mismo interruptor, requiere la contraseña) devuelve los archivos a su forma normal.

En Windows también existe el cifrado del propio sistema (EFS): es transparente para ti, para Mnema y para otros programas; la clave es tu cuenta de Windows y no está disponible en Windows Home.

## Historial y reversión

Cada entrada en la memoria queda registrada en un historial: quién la escribió, qué y cuándo. En la sección "Memoria" → "Historial", cualquier cambio se puede revertir con un solo botón. Si el archivo se modificó después, la reversión elimina únicamente las líneas de esa entrada y conserva las ediciones posteriores; solo se niega a hacerlo si esa misma línea ya fue corregida a mano. Antes de la primera edición de un archivo cada día, Mnema guarda una copia en 95 Saves y conserva las dos últimas. Las entradas del chat, del aprendizaje y de otras IA se procesan una por una, así que las escrituras simultáneas no se pisan entre sí. Si el archivo abierto en el editor de Mnema cambió mientras lo editabas, Mnema no lo sobrescribirá y te pedirá que lo abras de nuevo.

Si una regla se expresa con otras palabras ("Dame el resumen de la conversación breve" y "Haz los resúmenes cortos"), Mnema no añade una segunda línea, sino que reescribe la anterior con las nuevas palabras.

## Conectar otras IA

- Claude Code, Claude Desktop, Cursor: "Ajustes" → "IA y modelos" → "Memoria en otras IA" → "Conectar" en la tarjeta. La conexión se hace por MCP: memory_context, memory_search, memory_remember, memory_stale, memory_journal, memory_undo. El contexto se divide en partes de hasta 9 000 caracteres. Cursor solo recibe las reglas y los proyectos, y no escribe nada. En la tarjeta se ve si ya está conectado.
- ChatGPT y Gemini: en el chat de Mnema con tu propia clave (Ajustes → "IA y modelos" → tarjeta de OpenAI o Gemini → "Introducir clave"). No hay extensión para el navegador: todo lo que las propias IA no saben hacer, Mnema lo hace en tu ordenador.
- Por MCP, cada IA ve en el diario solo las entradas sobre lo que tiene permiso de leer, y deshace solo sus propias entradas. Tras actualizar desde la versión portátil, la conexión en Claude y Cursor pasa sola al nuevo programa.
- Modelos: "Ajustes" → "IA y modelos". Arriba, "Responde ahora": la medalla del modelo predeterminado y su selección. Debajo, "Modelos" en dos secciones: "De pago" (subsección "Por suscripción": Claude por suscripción; subsección "Con clave de API": ChatGPT, Claude · clave de API, DeepSeek, Gemini, OpenRouter, YandexGPT, con pago por consumo, aparte de la suscripción) y "Gratuitos" (el modelo integrado, Ollama y Strata, en este ordenador). Igual están divididos el menú de modelos de arriba a la izquierda y el paso "¿Con qué IA quieres hablar?" del primer inicio. Las tarjetas son medallas iguales con los colores de cada proveedor: el modelo integrado, Claude por suscripción, Claude · clave de API (Anthropic), ChatGPT (clave de API de OpenAI), Gemini, OpenRouter, Ollama. ChatGPT y Gemini se conectan solo con una clave de API: las suscripciones ChatGPT Plus y Gemini Advanced no dan clave, y la API se paga aparte a OpenAI y Google, según el consumo. La tarjeta de una IA conectada es de color y muestra el estado "conectado"; la de una no conectada es gris. La tarjeta tiene un solo botón: "Introducir clave" → el campo de la clave se abre directamente en la tarjeta → "Guardar y buscar modelos" o "Cancelar"; para Ollama, la dirección; para el modelo integrado, "Elegir y descargar". Claude por suscripción aparece solo si en el ordenador hay Claude Code: Mnema lo busca no solo en las rutas de búsqueda de programas, sino también donde lo instalan los instaladores (el oficial, npm, WinGet, Volta, bun, Homebrew) y dentro de la aplicación Claude Desktop. Si Claude Code se encuentra pero no has iniciado sesión en la cuenta, la tarjeta muestra el botón "Iniciar sesión": se abrirá la ventana de Claude Code, allí inicias sesión con la suscripción y después pulsas "Comprobar de nuevo". Si no se encuentra, aparece "Cómo instalar". Cada IA conectada tiene el botón "Desactivar": desaparece de todas las listas de modelos (chat, consorcio, "Con memoria y sin ella"), la clave y los ajustes se conservan, y "Activar" la devuelve. Si una IA está conectada pero no responde por un problema de la cuenta (se agotó el límite o la suscripción de Claude, no hay saldo en la cuenta, el inicio de sesión en Claude Code ha caducado, la clave no fue aceptada), la tarjeta muestra "no funciona" y el motivo, la IA desaparece de las listas y responde la siguiente que funcione. El botón "Comprobar de nuevo" hace una pequeña consulta real. El menú de modelos de arriba a la izquierda funciona igual para todas las IA: de cada una conectada muestra los tres mejores modelos (los completos más recientes, luego los ligeros mini y flash) y el enlace "Todos los modelos" con un contador. En "Todos los modelos" van primero los modelos operativos y, debajo de una línea, "Antiguos y de servicio": generaciones anteriores (gpt-3.5, gpt-4, Claude 3), copias con fecha, modelos para imágenes, voz y búsqueda. El modelo elegido se ve en el menú aunque no sea uno de los tres mejores. La clave y la comprobación están plegadas debajo de la lista. Cuando se agota un límite, Mnema vuelve a intentarlo sola al cabo de media hora. La clave se comprueba en el momento de guardarla: una clave incorrecta no cuenta como conectada. En "Memoria en otras IA", en la tarjeta de una IA conectada, por la línea Mnema → programa corre un punto.
- Modelo integrado: "Ajustes" → "IA y modelos" → "Modelo local".

## Proxy y VPN

Todo lo que sale a internet (modelos, búsqueda, descarga de modelos) pasa por un único proxy: el que hayas configurado en Mnema (primer inicio, menú de la bandeja "Proxy…", "Ajustes" → "Programa" → "VPN y proxy"); si no hay ninguno, el proxy del sistema (Windows; macOS: "Ajustes del Sistema" → "Red"; Linux: las variables https_proxy y la configuración de GNOME); y si tampoco hay, la conexión directa. Admite HTTP y SOCKS5 con usuario y contraseña, y la contraseña se guarda en el almacén seguro del sistema. VPN mediante clave: pega un enlace vless://, vmess://, trojan://, ss:// o una suscripción https://, y Mnema levantará Xray solo para ella misma ("Importar clave" desde el portapapeles o "Introducir clave manualmente"). También puedes usar un cliente VPN que ya tengas en marcha. "Comprobar" intenta llegar hasta Anthropic a través del proxy y te dice qué falla. El modelo integrado no pasa por el proxy.

## Ventana, bandeja, instalación

La primera vez que la abres, Mnema te hace una introducción corta: seis casos, con una sola idea por pantalla (no tienes que explicar las cosas de nuevo, una memoria en todas las IA, menos tokens en cualquier IA, reunión → tareas, recuerda decisiones y plazos, los secretos se quedan contigo), y la elección de IA. El caso de los tokens muestra la medición de la sección "Ahorro de tokens": una pregunta sobre un contrato de 153 000 caracteres, 29 643 tokens de entrada con todo el texto frente a 6 159 con Mnema. "Omitir" cierra la introducción al instante.

Al cerrar la ventana, esta se oculta en la bandeja y el aprendizaje continúa; la primera vez Mnema te pregunta "¿minimizar a la bandeja o salir?" y recuerda tu respuesta. "Salir" en el menú de la bandeja lo detiene todo. En el menú de la bandeja encontrarás: "Abrir Mnema", "Aprender ahora", "Pausar aprendizaje", "Proxy…" y el inicio automático ("Iniciar con Windows", en macOS "Abrir al iniciar sesión en macOS", en Linux "Iniciar al iniciar sesión"). Si vuelves a ejecutar el programa, no se abre una segunda copia, sino que se muestra la ventana de la primera. En Windows, Mnema elimina por sí misma de la bandeja, al arrancar, los iconos de procesos de Mnema que se hayan cerrado de forma abrupta. Si el escritorio de Linux no muestra la bandeja, al cerrar la ventana el programa se cierra.

El instalador instala Mnema sin permisos de administrador en %LOCALAPPDATA%\Programs\Mnema, detecta versiones anteriores y elimina solo sus archivos de programa: todo lo demás de esa carpeta (por ejemplo, una memoria creada junto al programa) se conserva. Desinstalar el programa tampoco borra la memoria. También hay una versión portátil en un archivo comprimido. El instalador todavía no tiene firma digital: Windows mostrará "Windows protegió su PC"; pulsa "Más información" → "Ejecutar de todos modos". En un Windows 10 limpio, Mnema instalará por sí misma el componente de ventana Microsoft WebView2 (hace falta internet una sola vez). macOS: imagen .dmg; arrastra Mnema a «Aplicaciones». El programa no está firmado por Apple, así que la primera vez ábrelo con clic derecho → «Abrir» (o Ajustes del Sistema → Privacidad y seguridad → «Abrir de todos modos»). Linux: un único archivo .AppImage (hazlo ejecutable y ábrelo) o un archivo .tar.gz con una carpeta. En Linux la ventana se dibuja con Qt; si no se abre, hacen falta los paquetes libxcb-cursor0 y libfuse2 (para AppImage).

Si al iniciar no encuentra la carpeta de la memoria (porque la moviste, le cambiaste el nombre o no está conectado el disco externo), Mnema te lo dice tal cual y te propone indicar dónde está ahora, volver a comprobar o empezar una memoria nueva. Las primeras pantallas aparecen en el idioma del sistema. Los errores de los servicios, Mnema los explica con palabras: qué ha pasado y qué hacer; el error permanece en la conversación, la respuesta interrumpida queda marcada y "Detener" libera la conversación de inmediato.

## Engranaje, tema, idioma, logros

El engranaje está arriba a la derecha: aprendizaje (arriba, el estado; con la memoria activada, ahí mismo está el interruptor para pausar el aprendizaje; con la memoria desactivada, solo aparece el texto "Memoria desactivada"; modo, feed), tema, idioma, logros (se pueden desactivar), "Cómo funciona Mnema" (tour), "Cómo funciona la memoria" (guía) y "Guía de Mnema". Las sugerencias desactivadas se recuperan aquí mismo: "Tutorial en conversaciones nuevas" y "Aviso de conversación costosa". La cruz de cualquier ventana es un círculo transparente con una cruz fina, del tamaño del signo "?"; Escape también cierra. En una conversación sin aprendizaje, el punto del engranaje es naranja; fuera de ella, vuelve a mostrar el estado del aprendizaje. El punto del engranaje indica el estado: verde — está aprendiendo, amarillo — la memoria está desactivada o el aprendizaje está en pausa, gris — solo aprende lo explícito o está desactivado. El estado del aprendizaje se ve en la barra de entrada: "Mnema aprende · memoria actualizada hace N min". Si no hay un modelo para analizar el habla, ahí aparece "Mnema solo recuerda lo dicho directamente": se guarda únicamente lo explícito ("recuerda …", correcciones, decisiones).

Nueve idiomas de interfaz: ruso, inglés, chino, español, hindi, portugués, francés, alemán, japonés. El modelo responde en el idioma elegido. Las conversaciones y la memoria no se traducen.

Logros: 99 recompensas en cinco grupos (primeros pasos, crecimiento de la memoria, ahorro y hábito, privacidad, poco comunes); la mayoría de los poco comunes están ocultos hasta que los consigues. La experiencia por las recompensas (10, 25, 50, 100) te da niveles desde "Novato" hasta "Memoria eterna".

En el engranaje está la "Guía de Mnema": es la guía dentro del programa, con secciones a la izquierda, búsqueda arriba y lo encontrado resaltado. Los ajustes siempre se abren en la primera sección, "IA y modelos". Al iniciarse, Mnema muestra durante un segundo una pantalla de bienvenida: el logotipo, el nombre y el lema "Free Memory AI Interface". El engranaje de la barra de entrada es pequeño, está arriba a la derecha junto al "?", y abre los ajustes de la barra de entrada.

## Varias memorias

En "Ajustes", a la izquierda, bajo las secciones, está el bloque "Memoria": todas las memorias de este equipo, con la abierta marcada con una marca de verificación. Al hacer clic en otra, se abre. "Nueva memoria" lleva a la primera pantalla, y la actual se queda en la lista. El menú ⋮ de cada memoria ofrece "Renombrar", que cambia el nombre en la lista (la carpeta en el disco conserva el suyo), y "Eliminar". La eliminación te pregunta dos veces: en la segunda ventana, "¿Eliminar definitivamente …?", se enumera lo que desaparecerá (retrato, datos, conversaciones, historial), y el botón "Eliminar" se activa a los 10 segundos: debajo de él va disminuyendo una barra roja y se muestra la cuenta atrás. La carpeta se mueve a la papelera, y puedes recuperarla desde allí. Si la memoria está abierta, Mnema primero la cierra y pasa a la siguiente de la lista; si no hay más, vuelve a la primera pantalla.

## Telegram

"Ajustes" → "Aprendizaje" → "Telegram". Mnema lee Telegram a través de su API y solo lee: el cliente de Telegram integrado en Mnema únicamente sabe iniciar sesión y leer, y cualquier otro comando (enviar, eliminar, marcar como leído, unirse, reaccionar) es rechazado por el propio programa antes de enviarse. El inicio de sesión funciona como en Telegram Desktop: api_id y api_hash de my.telegram.org (API development tools), número de teléfono, código de Telegram y contraseña en la nube, si la tienes. Debajo está "Chats para leer": "Añadir chats" abre la lista de tus chats personales y grupos con búsqueda, y marcas los que quieras. Mientras no haya ningún chat seleccionado, Mnema no lee nada. No se pueden seleccionar canales ni bots. En los chats seleccionados se lee la conversación completa: tus mensajes se marcan como "Yo" y los demás con el nombre de la otra persona, así Mnema te reconoce tanto a ti como a la gente que te rodea. El inicio de sesión se guarda cifrado en el almacén seguro del sistema; la lista de chats y lo aprendido, en la carpeta de memoria, y Mnema no tiene servidores propios. "Desconectar" borra el inicio de sesión; en Telegram la sesión permanece en "Dispositivos" hasta que la cierres allí.

## Tarjeta "Memoria" abajo a la izquierda

Dos filas, y cada una abre una prueba: "Memoria local en el PC" abre la carpeta de memoria, "Ajustes de acceso" abre la tabla «Qué ve cada IA». El engranaje de la tarjeta lleva a los ajustes de protección, y el "?" verde de al lado abre la guía "Cómo funciona la memoria", con 12 capítulos: el índice a la izquierda y, a la derecha, la escena, la explicación, un ejemplo (qué dices tú y qué pasa en la memoria) y el botón "Probar", que te lleva a un lugar real de la aplicación. Los capítulos: la carpeta en el ordenador, cómo está organizada la carpeta de memoria, la fecha de un dato (cuándo lo dijiste), aprender de las conversaciones, guardar al instante o preguntar (umbrales del 60 % y el 80 %), las correcciones se convierten en reglas, selección de lo necesario antes de responder, permisos de la IA, secretos, lo antiguo se vuelve a preguntar, historial con restauración, modelo en el ordenador. Al final, "Compruébalo tú": la carpeta, quién ve qué, qué ha salido al exterior.

Probar (menú "+" debajo del campo de entrada y página "Memoria"):
- "Primer encuentro": siete preguntas cortas: quién eres, dónde vives, qué es lo más importante ahora, proyectos, personas a tu alrededor, cómo hay que hablarte y qué no debe hacer nunca la IA. Las respuestas se guardan en la memoria como datos normales y no borran nada.
- "¿Cuánto te conoce Mnema?": un cuestionario de diez datos de la memoria: "Correcto" (el estado recibe la fecha de hoy), "Ya no es así" (escribes cómo es ahora y lo antiguo pasa al archivo de datos), "Falso" (el dato pasa al archivo). Al final, la puntuación.
- "Con memoria y sin ella": una pregunta a las IA conectadas (hasta tres); cada una responde dos veces: como un chat normal sin memoria y a través de Mnema. Las respuestas, lado a lado.
- "Asado": un consorcio en formato de asado (roast).

Cualquier resultado se puede convertir en una tarjeta con imagen ("Compartir"): copiarla, guardarla en "Imágenes/Mnema" o copiar el texto del post ya preparado con el enlace. En la imagen solo aparece lo que se ve en la ventana antes de enviarla.

## Lo que Mnema no puede hacer

- No ejecuta programas ni scripts. Con los archivos solo trabaja mediante acciones: en la carpeta de memoria y en las carpetas de trabajo, y cada una queda en el registro con opción de deshacerla.
- El cifrado con las herramientas del sistema (EFS) solo está disponible en Windows; el cifrado con contraseña de Mnema funciona en todos los sistemas.
- En un escaneo largo, reconoce solo las primeras 40 páginas.
- Sin internet, los modelos en la nube y la búsqueda no funcionan. Si la red se cae en mitad de una conversación, responde el modelo local de tu ordenador (si lo tienes descargado) y lo indica con una línea encima de la respuesta.
- No lee el correo ni el calendario mientras no le des la dirección y la contraseña, o un enlace.
