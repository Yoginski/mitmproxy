from __future__ import (absolute_import, print_function, division)

import struct

from construct import ConstructError

from netlib.tcp import NetLibError, NetLibInvalidCertificateError
from netlib.http.http1 import HTTP1Protocol
from ..contrib.tls._constructs import ClientHello, CipherSuites
from ..exceptions import ProtocolException
from .base import Layer


# taken from https://testssl.sh/openssl-rfc.mappping.html
CIPHER_ID_NAME_MAP = {
    0x00: 'NULL-MD5',
    0x01: 'NULL-MD5',
    0x02: 'NULL-SHA',
    0x03: 'EXP-RC4-MD5',
    0x04: 'RC4-MD5',
    0x05: 'RC4-SHA',
    0x06: 'EXP-RC2-CBC-MD5',
    0x07: 'IDEA-CBC-SHA',
    0x08: 'EXP-DES-CBC-SHA',
    0x09: 'DES-CBC-SHA',
    0x0a: 'DES-CBC3-SHA',
    0x0b: 'EXP-DH-DSS-DES-CBC-SHA',
    0x0c: 'DH-DSS-DES-CBC-SHA',
    0x0d: 'DH-DSS-DES-CBC3-SHA',
    0x0e: 'EXP-DH-RSA-DES-CBC-SHA',
    0x0f: 'DH-RSA-DES-CBC-SHA',
    0x10: 'DH-RSA-DES-CBC3-SHA',
    0x11: 'EXP-EDH-DSS-DES-CBC-SHA',
    0x12: 'EDH-DSS-DES-CBC-SHA',
    0x13: 'EDH-DSS-DES-CBC3-SHA',
    0x14: 'EXP-EDH-RSA-DES-CBC-SHA',
    0x15: 'EDH-RSA-DES-CBC-SHA',
    0x16: 'EDH-RSA-DES-CBC3-SHA',
    0x17: 'EXP-ADH-RC4-MD5',
    0x18: 'ADH-RC4-MD5',
    0x19: 'EXP-ADH-DES-CBC-SHA',
    0x1a: 'ADH-DES-CBC-SHA',
    0x1b: 'ADH-DES-CBC3-SHA',
    # 0x1c: ,
    # 0x1d: ,
    0x1e: 'KRB5-DES-CBC-SHA',
    0x1f: 'KRB5-DES-CBC3-SHA',
    0x20: 'KRB5-RC4-SHA',
    0x21: 'KRB5-IDEA-CBC-SHA',
    0x22: 'KRB5-DES-CBC-MD5',
    0x23: 'KRB5-DES-CBC3-MD5',
    0x24: 'KRB5-RC4-MD5',
    0x25: 'KRB5-IDEA-CBC-MD5',
    0x26: 'EXP-KRB5-DES-CBC-SHA',
    0x27: 'EXP-KRB5-RC2-CBC-SHA',
    0x28: 'EXP-KRB5-RC4-SHA',
    0x29: 'EXP-KRB5-DES-CBC-MD5',
    0x2a: 'EXP-KRB5-RC2-CBC-MD5',
    0x2b: 'EXP-KRB5-RC4-MD5',
    0x2f: 'AES128-SHA',
    0x30: 'DH-DSS-AES128-SHA',
    0x31: 'DH-RSA-AES128-SHA',
    0x32: 'DHE-DSS-AES128-SHA',
    0x33: 'DHE-RSA-AES128-SHA',
    0x34: 'ADH-AES128-SHA',
    0x35: 'AES256-SHA',
    0x36: 'DH-DSS-AES256-SHA',
    0x37: 'DH-RSA-AES256-SHA',
    0x38: 'DHE-DSS-AES256-SHA',
    0x39: 'DHE-RSA-AES256-SHA',
    0x3a: 'ADH-AES256-SHA',
    0x3b: 'NULL-SHA256',
    0x3c: 'AES128-SHA256',
    0x3d: 'AES256-SHA256',
    0x3e: 'DH-DSS-AES128-SHA256',
    0x3f: 'DH-RSA-AES128-SHA256',
    0x40: 'DHE-DSS-AES128-SHA256',
    0x41: 'CAMELLIA128-SHA',
    0x42: 'DH-DSS-CAMELLIA128-SHA',
    0x43: 'DH-RSA-CAMELLIA128-SHA',
    0x44: 'DHE-DSS-CAMELLIA128-SHA',
    0x45: 'DHE-RSA-CAMELLIA128-SHA',
    0x46: 'ADH-CAMELLIA128-SHA',
    0x62: 'EXP1024-DES-CBC-SHA',
    0x63: 'EXP1024-DHE-DSS-DES-CBC-SHA',
    0x64: 'EXP1024-RC4-SHA',
    0x65: 'EXP1024-DHE-DSS-RC4-SHA',
    0x66: 'DHE-DSS-RC4-SHA',
    0x67: 'DHE-RSA-AES128-SHA256',
    0x68: 'DH-DSS-AES256-SHA256',
    0x69: 'DH-RSA-AES256-SHA256',
    0x6a: 'DHE-DSS-AES256-SHA256',
    0x6b: 'DHE-RSA-AES256-SHA256',
    0x6c: 'ADH-AES128-SHA256',
    0x6d: 'ADH-AES256-SHA256',
    0x80: 'GOST94-GOST89-GOST89',
    0x81: 'GOST2001-GOST89-GOST89',
    0x82: 'GOST94-NULL-GOST94',
    0x83: 'GOST2001-GOST89-GOST89',
    0x84: 'CAMELLIA256-SHA',
    0x85: 'DH-DSS-CAMELLIA256-SHA',
    0x86: 'DH-RSA-CAMELLIA256-SHA',
    0x87: 'DHE-DSS-CAMELLIA256-SHA',
    0x88: 'DHE-RSA-CAMELLIA256-SHA',
    0x89: 'ADH-CAMELLIA256-SHA',
    0x8a: 'PSK-RC4-SHA',
    0x8b: 'PSK-3DES-EDE-CBC-SHA',
    0x8c: 'PSK-AES128-CBC-SHA',
    0x8d: 'PSK-AES256-CBC-SHA',
    # 0x8e: ,
    # 0x8f: ,
    # 0x90: ,
    # 0x91: ,
    # 0x92: ,
    # 0x93: ,
    # 0x94: ,
    # 0x95: ,
    0x96: 'SEED-SHA',
    0x97: 'DH-DSS-SEED-SHA',
    0x98: 'DH-RSA-SEED-SHA',
    0x99: 'DHE-DSS-SEED-SHA',
    0x9a: 'DHE-RSA-SEED-SHA',
    0x9b: 'ADH-SEED-SHA',
    0x9c: 'AES128-GCM-SHA256',
    0x9d: 'AES256-GCM-SHA384',
    0x9e: 'DHE-RSA-AES128-GCM-SHA256',
    0x9f: 'DHE-RSA-AES256-GCM-SHA384',
    0xa0: 'DH-RSA-AES128-GCM-SHA256',
    0xa1: 'DH-RSA-AES256-GCM-SHA384',
    0xa2: 'DHE-DSS-AES128-GCM-SHA256',
    0xa3: 'DHE-DSS-AES256-GCM-SHA384',
    0xa4: 'DH-DSS-AES128-GCM-SHA256',
    0xa5: 'DH-DSS-AES256-GCM-SHA384',
    0xa6: 'ADH-AES128-GCM-SHA256',
    0xa7: 'ADH-AES256-GCM-SHA384',
    0x5600: 'TLS_FALLBACK_SCSV',
    0xc001: 'ECDH-ECDSA-NULL-SHA',
    0xc002: 'ECDH-ECDSA-RC4-SHA',
    0xc003: 'ECDH-ECDSA-DES-CBC3-SHA',
    0xc004: 'ECDH-ECDSA-AES128-SHA',
    0xc005: 'ECDH-ECDSA-AES256-SHA',
    0xc006: 'ECDHE-ECDSA-NULL-SHA',
    0xc007: 'ECDHE-ECDSA-RC4-SHA',
    0xc008: 'ECDHE-ECDSA-DES-CBC3-SHA',
    0xc009: 'ECDHE-ECDSA-AES128-SHA',
    0xc00a: 'ECDHE-ECDSA-AES256-SHA',
    0xc00b: 'ECDH-RSA-NULL-SHA',
    0xc00c: 'ECDH-RSA-RC4-SHA',
    0xc00d: 'ECDH-RSA-DES-CBC3-SHA',
    0xc00e: 'ECDH-RSA-AES128-SHA',
    0xc00f: 'ECDH-RSA-AES256-SHA',
    0xc010: 'ECDHE-RSA-NULL-SHA',
    0xc011: 'ECDHE-RSA-RC4-SHA',
    0xc012: 'ECDHE-RSA-DES-CBC3-SHA',
    0xc013: 'ECDHE-RSA-AES128-SHA',
    0xc014: 'ECDHE-RSA-AES256-SHA',
    0xc015: 'AECDH-NULL-SHA',
    0xc016: 'AECDH-RC4-SHA',
    0xc017: 'AECDH-DES-CBC3-SHA',
    0xc018: 'AECDH-AES128-SHA',
    0xc019: 'AECDH-AES256-SHA',
    0xc01a: 'SRP-3DES-EDE-CBC-SHA',
    0xc01b: 'SRP-RSA-3DES-EDE-CBC-SHA',
    0xc01c: 'SRP-DSS-3DES-EDE-CBC-SHA',
    0xc01d: 'SRP-AES-128-CBC-SHA',
    0xc01e: 'SRP-RSA-AES-128-CBC-SHA',
    0xc01f: 'SRP-DSS-AES-128-CBC-SHA',
    0xc020: 'SRP-AES-256-CBC-SHA',
    0xc021: 'SRP-RSA-AES-256-CBC-SHA',
    0xc022: 'SRP-DSS-AES-256-CBC-SHA',
    0xc023: 'ECDHE-ECDSA-AES128-SHA256',
    0xc024: 'ECDHE-ECDSA-AES256-SHA384',
    0xc025: 'ECDH-ECDSA-AES128-SHA256',
    0xc026: 'ECDH-ECDSA-AES256-SHA384',
    0xc027: 'ECDHE-RSA-AES128-SHA256',
    0xc028: 'ECDHE-RSA-AES256-SHA384',
    0xc029: 'ECDH-RSA-AES128-SHA256',
    0xc02a: 'ECDH-RSA-AES256-SHA384',
    0xc02b: 'ECDHE-ECDSA-AES128-GCM-SHA256',
    0xc02c: 'ECDHE-ECDSA-AES256-GCM-SHA384',
    0xc02d: 'ECDH-ECDSA-AES128-GCM-SHA256',
    0xc02e: 'ECDH-ECDSA-AES256-GCM-SHA384',
    0xc02f: 'ECDHE-RSA-AES128-GCM-SHA256',
    0xc030: 'ECDHE-RSA-AES256-GCM-SHA384',
    0xc031: 'ECDH-RSA-AES128-GCM-SHA256',
    0xc032: 'ECDH-RSA-AES256-GCM-SHA384',
    0xcc13: 'ECDHE-RSA-CHACHA20-POLY1305',
    0xcc14: 'ECDHE-ECDSA-CHACHA20-POLY1305',
    0xcc15: 'DHE-RSA-CHACHA20-POLY1305',
    0xff00: 'GOST-MD5',
    0xff01: 'GOST-GOST94',
    0xff02: 'GOST-GOST89MAC',
    0xff03: 'GOST-GOST89STREAM',
    0x010080: 'RC4-MD5',
    0x020080: 'EXP-RC4-MD5',
    0x030080: 'RC2-CBC-MD5',
    0x040080: 'EXP-RC2-CBC-MD5',
    0x050080: 'IDEA-CBC-MD5',
    0x060040: 'DES-CBC-MD5',
    0x0700c0: 'DES-CBC3-MD5',
    0x080080: 'RC4-64-MD5',
}

def is_tls_record_magic(d):
    """
    Returns:
        True, if the passed bytes start with the TLS record magic bytes.
        False, otherwise.
    """
    d = d[:3]

    # TLS ClientHello magic, works for SSLv3, TLSv1.0, TLSv1.1, TLSv1.2
    # http://www.moserware.com/2009/06/first-few-milliseconds-of-https.html#client-hello
    return (
        len(d) == 3 and
        d[0] == '\x16' and
        d[1] == '\x03' and
        d[2] in ('\x00', '\x01', '\x02', '\x03')
    )


class TlsLayer(Layer):
    def __init__(self, ctx, client_tls, server_tls):
        self.client_sni = None
        self.client_alpn_protocols = None

        super(TlsLayer, self).__init__(ctx)
        self._client_tls = client_tls
        self._server_tls = server_tls

        self._sni_from_server_change = None

    def __call__(self):
        """
        The strategy for establishing SSL is as follows:
            First, we determine whether we need the server cert to establish ssl with the client.
            If so, we first connect to the server and then to the client.
            If not, we only connect to the client and do the server_ssl lazily on a Connect message.

        An additional complexity is that establish ssl with the server may require a SNI value from the client.
        In an ideal world, we'd do the following:
            1. Start the SSL handshake with the client
            2. Check if the client sends a SNI.
            3. Pause the client handshake, establish SSL with the server.
            4. Finish the client handshake with the certificate from the server.
        There's just one issue: We cannot get a callback from OpenSSL if the client doesn't send a SNI. :(
        Thus, we manually peek into the connection and parse the ClientHello message to obtain both SNI and ALPN values.

        Further notes:
            - OpenSSL 1.0.2 introduces a callback that would help here:
              https://www.openssl.org/docs/ssl/SSL_CTX_set_cert_cb.html
            - The original mitmproxy issue is https://github.com/mitmproxy/mitmproxy/issues/427
        """

        client_tls_requires_server_cert = (
            self._client_tls and self._server_tls and not self.config.no_upstream_cert
        )

        if self._client_tls:
            self._parse_client_hello()

        if client_tls_requires_server_cert:
            self._establish_tls_with_client_and_server()
        elif self._client_tls:
            self._establish_tls_with_client()

        layer = self.ctx.next_layer(self)
        layer()

    def __repr__(self):
        if self._client_tls and self._server_tls:
            return "TlsLayer(client and server)"
        elif self._client_tls:
            return "TlsLayer(client)"
        elif self._server_tls:
            return "TlsLayer(server)"
        else:
            return "TlsLayer(inactive)"

    def _get_client_hello(self):
        """
        Peek into the socket and read all records that contain the initial client hello message.

        Returns:
            The raw handshake packet bytes, without TLS record header(s).
        """
        client_hello = ""
        client_hello_size = 1
        offset = 0
        while len(client_hello) < client_hello_size:
            record_header = self.client_conn.rfile.peek(offset + 5)[offset:]
            if not is_tls_record_magic(record_header) or len(record_header) != 5:
                raise ProtocolException('Expected TLS record, got "%s" instead.' % record_header)
            record_size = struct.unpack("!H", record_header[3:])[0] + 5
            record_body = self.client_conn.rfile.peek(offset + record_size)[offset + 5:]
            if len(record_body) != record_size - 5:
                raise ProtocolException("Unexpected EOF in TLS handshake: %s" % record_body)
            client_hello += record_body
            offset += record_size
            client_hello_size = struct.unpack("!I", '\x00' + client_hello[1:4])[0] + 4
        return client_hello

    def _parse_client_hello(self):
        """
        Peek into the connection, read the initial client hello and parse it to obtain ALPN values.
        """
        try:
            raw_client_hello = self._get_client_hello()[4:]  # exclude handshake header.
        except ProtocolException as e:
            self.log("Cannot parse Client Hello: %s" % repr(e), "error")
            return

        try:
            client_hello = ClientHello.parse(raw_client_hello)
        except ConstructError as e:
            self.log("Cannot parse Client Hello: %s" % repr(e), "error")
            self.log("Raw Client Hello:\r\n:%s" % raw_client_hello.encode("hex"), "debug")
            return

        self.client_ciphers = client_hello.cipher_suites.cipher_suites

        for extension in client_hello.extensions:
            if extension.type == 0x00:
                if len(extension.server_names) != 1 or extension.server_names[0].type != 0:
                    self.log("Unknown Server Name Indication: %s" % extension.server_names, "error")
                self.client_sni = extension.server_names[0].name
            elif extension.type == 0x10:
                self.client_alpn_protocols = list(extension.alpn_protocols)

        self.log(
            "Parsed Client Hello: sni=%s, alpn=%s" % (self.client_sni, self.client_alpn_protocols),
            "debug"
        )

    def connect(self):
        if not self.server_conn:
            self.ctx.connect()
        if self._server_tls and not self.server_conn.tls_established:
            self._establish_tls_with_server()

    def set_server(self, address, server_tls=None, sni=None):
        if server_tls is not None:
            self._sni_from_server_change = sni
            self._server_tls = server_tls
        self.ctx.set_server(address, None, None)

    @property
    def sni_for_server_connection(self):
        if self._sni_from_server_change is False:
            return None
        else:
            return self._sni_from_server_change or self.client_sni

    @property
    def alpn_for_client_connection(self):
        return self.server_conn.get_alpn_proto_negotiated()

    def __alpn_select_callback(self, conn_, options):
        """
        Once the client signals the alternate protocols it supports,
        we reconnect upstream with the same list and pass the server's choice down to the client.
        """

        # This gets triggered if we haven't established an upstream connection yet.
        default_alpn = HTTP1Protocol.ALPN_PROTO_HTTP1
        # alpn_preference = netlib.http.http2.HTTP2Protocol.ALPN_PROTO_H2

        if self.alpn_for_client_connection in options:
            choice = bytes(self.alpn_for_client_connection)
        elif default_alpn in options:
            choice = bytes(default_alpn)
        else:
            choice = options[0]
        self.log("ALPN for client: %s" % choice, "debug")
        return choice

    def _establish_tls_with_client_and_server(self):
        self.ctx.connect()

        # If establishing TLS with the server fails, we try to establish TLS with the client nonetheless
        # to send an error message over TLS.
        try:
            self._establish_tls_with_server()
        except Exception as e:
            try:
                self._establish_tls_with_client()
            except:
                pass
            raise e

        self._establish_tls_with_client()

    def _establish_tls_with_client(self):
        self.log("Establish TLS with client", "debug")
        cert, key, chain_file = self._find_cert()

        try:
            self.client_conn.convert_to_ssl(
                cert, key,
                method=self.config.openssl_method_client,
                options=self.config.openssl_options_client,
                cipher_list=self.config.ciphers_client,
                dhparams=self.config.certstore.dhparams,
                chain_file=chain_file,
                alpn_select_callback=self.__alpn_select_callback,
            )
        except NetLibError as e:
            raise ProtocolException("Cannot establish TLS with client: %s" % repr(e), e)

    def _establish_tls_with_server(self):
        self.log("Establish TLS with server", "debug")
        try:
            # We only support http/1.1 and h2.
            # If the server only supports spdy (next to http/1.1), it may select that
            # and mitmproxy would enter TCP passthrough mode, which we want to avoid.
            deprecated_http2_variant = lambda x: x.startswith("h2-") or x.startswith("spdy")
            if self.client_alpn_protocols:
                alpn = filter(lambda x: not deprecated_http2_variant(x), self.client_alpn_protocols)
            else:
                alpn = None

            ciphers_server = self.config.ciphers_server
            if not ciphers_server:
                ciphers_server = []
                for id in self.client_ciphers:
                    if id in CIPHER_ID_NAME_MAP.keys():
                        ciphers_server.append(CIPHER_ID_NAME_MAP[id])
                ciphers_server = ':'.join(ciphers_server)

            self.server_conn.establish_ssl(
                self.config.clientcerts,
                self.sni_for_server_connection,
                method=self.config.openssl_method_server,
                options=self.config.openssl_options_server,
                verify_options=self.config.openssl_verification_mode_server,
                ca_path=self.config.openssl_trusted_cadir_server,
                ca_pemfile=self.config.openssl_trusted_ca_server,
                cipher_list=ciphers_server,
                alpn_protos=alpn,
            )
            tls_cert_err = self.server_conn.ssl_verification_error
            if tls_cert_err is not None:
                self.log(
                    "TLS verification failed for upstream server at depth %s with error: %s" %
                    (tls_cert_err['depth'], tls_cert_err['errno']),
                    "error")
                self.log("Ignoring server verification error, continuing with connection", "error")
        except NetLibInvalidCertificateError as e:
            tls_cert_err = self.server_conn.ssl_verification_error
            self.log(
                "TLS verification failed for upstream server at depth %s with error: %s" %
                (tls_cert_err['depth'], tls_cert_err['errno']),
                "error")
            self.log("Aborting connection attempt", "error")
            raise ProtocolException("Cannot establish TLS with {address} (sni: {sni}): {e}".format(
                address=repr(self.server_conn.address),
                sni=self.sni_for_server_connection,
                e=repr(e),
            ), e)
        except NetLibError as e:
            raise ProtocolException("Cannot establish TLS with {address} (sni: {sni}): {e}".format(
                address=repr(self.server_conn.address),
                sni=self.sni_for_server_connection,
                e=repr(e),
            ), e)

        self.log("ALPN selected by server: %s" % self.alpn_for_client_connection, "debug")

    def _find_cert(self):
        host = self.server_conn.address.host
        sans = set()
        # Incorporate upstream certificate
        use_upstream_cert = (
            self.server_conn and
            self.server_conn.tls_established and
            (not self.config.no_upstream_cert)
        )
        if use_upstream_cert:
            upstream_cert = self.server_conn.cert
            sans.update(upstream_cert.altnames)
            if upstream_cert.cn:
                sans.add(host)
                host = upstream_cert.cn.decode("utf8").encode("idna")
        # Also add SNI values.
        if self.client_sni:
            sans.add(self.client_sni)
        if self._sni_from_server_change:
            sans.add(self._sni_from_server_change)

        sans.discard(host)
        return self.config.certstore.get_cert(host, list(sans))