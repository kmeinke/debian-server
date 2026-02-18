firewall:
  tcp_ports:
    - 22
    - 80
    - 443
  egress:
    tcp_ports:
      - 53    # DNS
      - 443   # APT, HTTPS
      - 587   # SMTP submission (STARTTLS)
      - 465   # SMTP submission (implicit TLS)
    udp_ports:
      - 53    # DNS
      - 123   # NTP
