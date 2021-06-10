Размер рабочего поля взят с оригинального терминала Fallout-3 - 25 строк и 80 столбцов, нужный размер подгоняется размерами консольного шрифта.

Для запуска терминала необходимо иметь установленный python версии 3.6 или старше, модули к нему – pygame, curses, jSON. Единственная запускаемая программа – f3termCurses.py Управление производится через внесение изменений в текстовый файл ftjSON.txtс в jSON формате с помощью любого текстового редактора. Параметры комментированы прямо в базе (единственная таблица – имя параметра, значение, комментарий) Основные моменты. Для входа терминала в режим взлома (основной режим) параметры isHacked и isLocked должны иметь значение false, параметр isPowerOn – значение true. Параметр wordsPrinted – число слов, включая пароль, отображаемых на экране (16 - оптимальное значение). Параметр wordLength – длина слова, может быть 6, 8, 10, 12 – чем длиннее, тем сложнее. Размер рабочего поля (экрана) в символах для оптимального отображения – 80х25. Читы работают, как и в оригинальных терминалах.

После успешного взлома - показывается меню выбора текстовых фрагментов, кодирвоанное в параметре "textMenu" конфига. Формат параметра - хэш вида "Заголовок":{"type": "text", "name": "Имя файла"}. После выбора заголовка демонстрируется текст из соответствующего файла. ВНИМАНИЕ!!! Текст должен быть отформатирован переводами строки так, чтобы каждая строка не превышала 79 символов! Для Linux текст по умолчанию должен быть в кодировке UTF-8, как в примере.

Пролистывание текста - PgUp и PgDown (дублируется W и S соответственно). Двойной ESC (под Linux), Одинарный ESC (винда) или BACKSPACE - возврат в меню.

Всё управление, там где стрелки, также дублировано на WASD.
