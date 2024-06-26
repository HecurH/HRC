salt = 'morskaya'

mail_settings = {
    'server': 'smtp.mail.ru',
    'port': 465,
    'email': 'EMAIL',
    'password': 'PASSWORD'
}


mail_text_register = """\
Уважаемый пользователь,

Благодарим вас за регистрацию в HRC. Мы рады приветствовать вас в нашем сообществе!

Ваш логин для входа: [логин]
Пароль: [пароль]

Пожалуйста, обратите внимание, что ваш пароль был сгенерирован случайным образом для обеспечения безопасности вашей учетной записи. Рекомендуем вам изменить пароль после первого входа в систему.

Также, в приложении к этому письму, вы найдете файл с вашим приватным ключом. Пожалуйста, сохраните этот файл в надежном месте и не передавайте его третьим лицам. Приватный ключ необходим для обеспечения безопасности ваших персональных сообщений.

Если у вас возникнут вопросы или проблемы, не стесняйтесь обращаться к нашей службе поддержки.

С уважением,
Поддержка мессенджера "Зонт" """

mail_text_warn = """\
Уважаемый пользователь,

Мы обращаем ваше внимание на подозрительную активность в вашем аккаунте мессенджера "Зонт". Недавно была зафиксирована попытка входа с другого IP-адреса. Примерное расположение и IP-адрес устройства, с которого производилась попытка входа, указаны ниже:

Местоположение: [loc]
IP-адрес: [ip]

Для защиты вашей учетной записи рекомендуем принять меры безопасности, например, изменить пароль или включить двухфакторную аутентификацию.

С уважением,
Поддержка мессенджера "Зонт" """


