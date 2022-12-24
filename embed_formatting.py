def embed_formatting(message) -> str:
    note = message['text']
    formats = {'bold': '**',
                'italic': '_',
                'underline': '==',
                'strikethrough': '~~',
                'spoiler': '',
                'code': '`',
    }
    formatted_note = ''
    tail = 0
    try:
        for entity in message['entities']:
            start_pos = entity['offset']
            end_pos = start_pos + entity['length']
            # добавляем неформатированный кусок сообщения, если он есть
            if start_pos > tail:
                formatted_note += note[tail:start_pos]
                tail = start_pos
            # обрабатываем простые entity с симметричным форматированием
            if entity['type'] in formats:
                format_code = formats[entity['type']]
                formatted_note += format_code + note[start_pos:end_pos] + format_code
            # обрабатываем сложные entity с несимметричным форматированием
            # Пока не сделано
            elif True:
                formatted_note += note[start_pos:end_pos]
            tail = end_pos
    except:
        formatted_note = note
    return formatted_note

message = [('message_id', 136), ('from', {'id': 33383886, 'is_bot': False, 'first_name': 'Dmitry', 'last_name': 'Nik', 'username': 'dimonier', 'language_code': 'en', 'is_premium': True}), ('chat', {'id': -807853408, 'title': 'Диктофон', 'type': 'group', 'all_members_are_administrators': True}), ('date', 1671664088), ('text', 'Привет! Это болд, это италик.\nА это вообще ссылка.'), ('entities', {{'type': 'bold', 'offset': 12, 'length': 4}, {'type': 'italic', 'offset': 22, 'length': 6}, {'type': 'text_link', 'offset': 32, 'length': 17, 'url': 'https://ya.ru/'}})]

print(embed_formatting(message))
