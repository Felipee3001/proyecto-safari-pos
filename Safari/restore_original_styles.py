with open('Safari/static/estilos.css/login.css', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find(':root {')
orig_login_css = text[idx:].strip()

with open('Safari/static/estilos.css/admin.css', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find(':root {')
orig_admin_css = text[idx:].strip()

with open('Safari/static/estilos.css/prototipo.css', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find('/* --- ESTILOS DE IDENTIDAD CORPORATIVA --- */')
orig_proto_css = text[idx:].strip()

# 1. Restore login.html
with open('Safari/templates/login.html', 'r', encoding='utf-8') as f:
    l_html = f.read()

# Remove bootstrap links and styles
start_head = l_html.find('<title>Acceso Administrativo Safari</title>') + len('<title>Acceso Administrativo Safari</title>')
end_head = l_html.find('</head>')

new_l_head = f"""
    <style>
{orig_login_css}
    </style>
"""
l_html = l_html[:start_head] + new_l_head + l_html[end_head:]
l_html = l_html.replace('<body class="safari-login-body">', '<body>')
l_html = l_html.replace('    <!-- Bootstrap 5 JS Bundle -->\n    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n', '')

with open('Safari/templates/login.html', 'w', encoding='utf-8') as f:
    f.write(l_html)
print("login.html restored!")

# 2. Restore admin.html
with open('Safari/templates/admin.html', 'r', encoding='utf-8') as f:
    a_html = f.read()

start_head = a_html.find('<link rel="icon" href="data:,">') + len('<link rel="icon" href="data:,">')
end_head = a_html.find('</head>')

new_a_head = f"""
    <style>
{orig_admin_css}
    </style>
"""
a_html = a_html[:start_head] + new_a_head + a_html[end_head:]
a_html = a_html.replace('<body class="safari-admin-body">', '<body>')
a_html = a_html.replace('    <!-- Bootstrap 5 JS Bundle -->\n    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n', '')

with open('Safari/templates/admin.html', 'w', encoding='utf-8') as f:
    f.write(a_html)
print("admin.html restored!")

# 3. Restore prototipo.html
with open('Safari/templates/prototipo.html', 'r', encoding='utf-8') as f:
    p_html = f.read()

start_head = p_html.find('<link rel="icon" href="data:,">') + len('<link rel="icon" href="data:,">')
end_head = p_html.find('</head>')

new_p_head = f"""
    <style>
{orig_proto_css}
    </style>
"""
p_html = p_html[:start_head] + new_p_head + p_html[end_head:]
p_html = p_html.replace('<body class="safari-prototipo-body">', '<body>')
p_html = p_html.replace('    <!-- Bootstrap 5 JS Bundle -->\n    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n', '')

with open('Safari/templates/prototipo.html', 'w', encoding='utf-8') as f:
    f.write(p_html)
print("prototipo.html restored!")

