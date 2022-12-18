import asyncio
import socket

from email._header_value_parser import get_addr_spec, get_angle_addr

class SMTPServerProtocol(asyncio.Protocol):

    COMMAND = 0
    DATA = 1

    def __init__(self):
        # イベントループを取得
        self.loop = asyncio.get_event_loop()
        # キャンセル用にcall_laterの戻り値を保持
        self._timeout_handle = None
        # ホスト名
        self.fqdn = socket.getfqdn()
        self.smtp_state = self.COMMAND
        self.seen_greeting = ''
        self.extended_smtp = False

        self.mailfrom = None
        self.rcpttos = []
        self.mail_options = ''
        self.rcpt_options = ''
        self.received_data = b''


    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self._reset_timeout()

        # 最初のメッセージ
        self.send('220 {} Python SMTP proxy version 0.1'.format(self.fqdn))


    def data_received(self, data):

        #タイムアウトのカウンターリセット
        self._reset_timeout()

        # コマンド入力時の処理
        if self.smtp_state == self.COMMAND:
            if not data:
                self.send('500 Error: bad syntax')
                return
            try:
                line = data.decode().strip()
            except:
                self.transport.close()
                return

            # コマンド解析
            i = line.find(' ')
            if i < 0:
                command = line.upper()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i+1:].strip()

            # コマンドに対応するメソッド呼び出し
            method = getattr(self, 'smtp_' + command, None)
            if not method:
                self.send('500 Error: command "%s" not recognized' % command)
                return

            method(arg)

        
        # DATA受付部分の処理
        else:
            if self.smtp_state != self.DATA:
                self.send('451 Internal confusion')
                return

            self.received_data += data
            if not self.received_data.endswith(b'\r\n.\r\n'):
                return

            self.received_data = self.received_data[:-5].replace(b'\r\n', b'\n')
            args = (self, self.mailfrom, self.rcpttos, self.received_data)
            kwargs = {
                'mail_options': self.mail_options,
                'rcpt_options': self.rcpt_options,
            }
            status = self.process_message(*args, **kwargs)
            self._set_post_data_state()
            if not status:
                self.send('250 OK')
            else:
                self.send(status)



    # データ送信
    def send(self, message):
        if isinstance(message, str):
            message = message.encode('utf-8') + b'\n'
        self.transport.write(message)

    # メール受信イベントu
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Override this abstract method to handle messages from the client."""
        raise NotImplementedError


    # -------------------------------------------------------------
    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        if not arg:
            self.send('501 Syntax: HELO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            self.send('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.seen_greeting = arg
        self.send('250 %s' % self.fqdn)

    def smtp_EHLO(self, arg):
        if not arg:
            self.send('501 Syntax: EHLO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            self.send('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.seen_greeting = arg
        self.extended_smtp = True
        self.send('250-%s' % self.fqdn)
        self.send('250 HELP')

    def smtp_NOOP(self, arg):
        if arg:
            self.send('501 Syntax: NOOP')
        else:
            self.send('250 OK')

    def smtp_QUIT(self, arg):
        # args is ignored
        self.send('221 Bye')
        self.transport.close()

    def smtp_HELP(self, arg):
        if arg:
            extended = ' [SP <mail-parameters>]'
            lc_arg = arg.upper()
            if lc_arg == 'EHLO':
                self.send('250 Syntax: EHLO hostname')
            elif lc_arg == 'HELO':
                self.send('250 Syntax: HELO hostname')
            elif lc_arg == 'MAIL':
                msg = '250 Syntax: MAIL FROM: <address>'
                if self.extended_smtp:
                    msg += extended
                self.send(msg)
            elif lc_arg == 'RCPT':
                msg = '250 Syntax: RCPT TO: <address>'
                if self.extended_smtp:
                    msg += extended
                self.send(msg)
            elif lc_arg == 'DATA':
                self.send('250 Syntax: DATA')
            elif lc_arg == 'RSET':
                self.send('250 Syntax: RSET')
            elif lc_arg == 'NOOP':
                self.send('250 Syntax: NOOP')
            elif lc_arg == 'QUIT':
                self.send('250 Syntax: QUIT')
            elif lc_arg == 'VRFY':
                self.send('250 Syntax: VRFY <address>')
            else:
                self.send('501 Supported commands: EHLO HELO MAIL RCPT '
                          'DATA RSET NOOP QUIT VRFY')
        else:
            self.send('250 Supported commands: EHLO HELO MAIL RCPT DATA '
                      'RSET NOOP QUIT VRFY')

    def smtp_VRFY(self, arg):
        if arg:
            address, params = self._getaddr(arg)
            if address:
                self.send('252 Cannot VRFY user, but will accept message '
                          'and attempt delivery')
            else:
                self.send('502 Could not VRFY %s' % arg)
        else:
            self.send('501 Syntax: VRFY <address>')


    def smtp_MAIL(self, arg):
        if not self.seen_greeting:
            self.send('503 Error: send HELO first')
            return
        
        syntaxerr = '501 Syntax: MAIL FROM: <address>'
        if self.extended_smtp:
            syntaxerr += ' [SP <mail-parameters>]'
        if arg is None:
            self.send(syntaxerr)
            return

        arg = self._strip_command_keyword('FROM:', arg)
        address, params = self._getaddr(arg)
        if not address:
            self.send(syntaxerr)
            return
        if not self.extended_smtp and params:
            self.send(syntaxerr)
            return
        if self.mailfrom:
            self.send('503 Error: nested MAIL command')
            return
        
        self.mail_options = params.upper().split()
        params = self._getparams(self.mail_options)
        if params is None:
            self.send(syntaxerr)
            return

        body = params.pop('BODY', '7BIT')
        if body not in ['7BIT', '8BITMIME']:
            self.send('501 Error: BODY can only be one of 7BIT, 8BITMIME')
            return

        size = params.pop('SIZE', None)
        if size:
            if not size.isdigit():
                self.send(syntaxerr)
                return
            elif self.data_size_limit and int(size) > self.data_size_limit:
                self.send('552 Error: message size exceeds fixed maximum message size')
                return
        if len(params.keys()) > 0:
            self.send('555 MAIL FROM parameters not recognized or not implemented')
            return
        self.mailfrom = address
        self.send('250 OK')


    def smtp_RCPT(self, arg):
        if not self.seen_greeting:
            self.send('503 Error: send HELO first');
            return

        if not self.mailfrom:
            self.send('503 Error: need MAIL command')
            return
        syntaxerr = '501 Syntax: RCPT TO: <address>'
        if self.extended_smtp:
            syntaxerr += ' [SP <mail-parameters>]'
        if arg is None:
            self.send(syntaxerr)
            return
        arg = self._strip_command_keyword('TO:', arg)
        address, params = self._getaddr(arg)
        if not address:
            self.send(syntaxerr)
            return
        if not self.extended_smtp and params:
            self.send(syntaxerr)
            return
        if not self.extended_smtp and params:
            self.send(syntaxerr)
            return
        self.rcpt_options = params.upper().split()
        params = self._getparams(self.rcpt_options)
        if params is None:
            self.send(syntaxerr)
            return
        # XXX currently there are no options we recognize.
        if len(params.keys()) > 0:
            self.send('555 RCPT TO parameters not recognized or not implemented')
            return
        self.rcpttos.append(address)
        self.send('250 OK')


    def smtp_RSET(self, arg):
        if arg:
            self.send('501 Syntax: RSET')
            return
        self._set_rset_state()
        self.send('250 OK')

    def smtp_DATA(self, arg):
        if not self.seen_greeting:
            self.send('503 Error: send HELO first');
            return
        if not self.rcpttos:
            self.send('503 Error: need RCPT command')
            return
        if arg:
            self.send('501 Syntax: DATA')
            return
        self.smtp_state = self.DATA
        #self.set_terminator(b'\r\n.\r\n')
        self.send('354 End data with <CR><LF>.<CR><LF>')

    # Commands that have not been implemented
    def smtp_EXPN(self, arg):
        self.send('502 EXPN not implemented')

    # -------------------------------------------------------------


    def _strip_command_keyword(self, keyword, arg):
        keylen = len(keyword)
        if arg[:keylen].upper() == keyword:
            return arg[keylen:].strip()
        return ''

    def _getaddr(self, arg):
        if not arg:
            return '', ''
        if arg.lstrip().startswith('<'):
            address, rest = get_angle_addr(arg)
        else:
            address, rest = get_addr_spec(arg)
        if not address:
            return address, rest
        return address.addr_spec, rest

    def _getparams(self, params):
        # Return params as dictionary. Return None if not all parameters
        # appear to be syntactically valid according to RFC 1869.
        result = {}
        for param in params:
            param, eq, value = param.partition('=')
            if not param.isalnum() or eq and not value:
                return None
            result[param] = value if eq else True
        return result

    def _set_post_data_state(self):
        """Reset state variables to their post-DATA state."""
        self.smtp_state = self.COMMAND
        self.mailfrom = None
        self.rcpttos = []

    def _set_rset_state(self):
        """Reset all state variables except the greeting."""
        self._set_post_data_state()
        self.received_data = b''
    
    # コールバック呼び出し予約
    def _reset_timeout(self):
        # 前回のタイムアウトコールバック予約をキャンセル
        if self._timeout_handle:
            self._timeout_handle.cancel()

        # 300秒後にコールバックを呼び出し
        self._timeout_handle = self.loop.call_later(
            300, self._timeout_callback
        )

    # タイムアウト コネクション切断
    def _timeout_callback(self):
        self.send('Connection timeout')
        self.transport.close()


