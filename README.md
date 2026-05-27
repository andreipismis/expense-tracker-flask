📊 Expense Tracker App

O aplicație web dezvoltată în Python (Flask) pentru gestionarea inteligentă a finanțelor personale. Permite monitorizarea veniturilor, cheltuielilor și colaborarea pe bugete comune.



🚀 Funcționalități Principale

* Autentificare Securizată: Sistem de login/register cu parole hash-uite (PBKDF2 SHA-256) și gestiunea sesiunilor via Flask-Login.
* Managementul Bugetelor: Crearea și ștergerea portofoliilor financiare, cu evidența soldului inițial și calculul automat al balanței curente.
* Colaborare (Shared Budgets): Posibilitatea de a adăuga alți utilizatori într-un buget comun (interogări asincrone AJAX), utilizând o relație Many-to-Many.
* Monitorizarea Tranzacțiilor: Adăugarea de venituri și cheltuieli clasificate pe categorii.
* Rapoarte Financiare: Dashboard analitic cu calculul balanței nete și detalierea vizuală a cheltuielilor/veniturilor pe categorii în funcție de perioada selectată.
* Integritatea Datelor: Ștergere în cascadă (Cascade Deletion) implementată în backend pentru a preveni înregistrările orfane în baza de date.



🛠️ Stiva Tehnologică (Tech Stack)

* Backend: Python 3, Flask
* Bază de date: SQLite
* ORM: Flask-SQLAlchemy
* Frontend: HTML5, CSS3 (Flexbox/Grid), JavaScript Vanilla
* Securitate: Werkzeug Security, ItsDangerous



💻 Instalare și Rulare Locală

Urmează acești pași pentru a rula aplicația pe mașina ta locală:



1\. Clonează repository-ul:

`git clone https://github.com/NUMELE\_TAU/expense-tracker-flask.git`
`cd expense-tracker-flask`



2\. Creează și activează un mediu virtual:

Pe Windows:

`python -m venv venv`
`venv\\Scripts\\activate`



Pe macOS/Linux:

`python3 -m venv venv`

`source venv/bin/activate`



3\. Instalează dependențele:

`pip install -r requirements.txt`



4\. Rulează aplicația:

`python app.py`



(Notă: La prima rulare, baza de date expense\_tracker.db va fi generată automat pe baza modelelor definite.)



5\. Accesează aplicația:

Deschide browserul și navighează la adresa: `http://127.0.0.1:5000`

