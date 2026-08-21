# Import du backup MySQL vers PostgreSQL

Ce dossier contient un outil independant : il ne modifie pas les fichiers de l'application.

1. Configurez `DATABASE_PUBLIC_URL` avec l'URL de votre PostgreSQL Railway.
2. Creez le schema PostgreSQL avec `python manage.py migrate`.
3. Verifiez d'abord le backup, sans ecriture :

   ```powershell
   $env:DATABASE_PUBLIC_URL="postgresql://..."
   python tools/import_mysql_dump_to_postgres.py --dry-run
   ```

4. Si la verification est reussie et que la base est vide, lancez :

   ```powershell
   python tools/import_mysql_dump_to_postgres.py
   ```

Le script execute tout l'import dans une transaction : en cas d'erreur, aucune donnee n'est validee. Il refuse aussi une table deja remplie, sauf avec `--allow-nonempty`. Il reconnait egalement les anciennes colonnes devenues des references Django, par exemple `sexe` vers `sexe_id`, et convertit les booleens MySQL (`0` et `1`) au format PostgreSQL.

Il ne copie pas `depense_categoriedepense`, `django_migrations` ni les sessions temporaires `django_session`.
Les deux dernieres tables doivent rester gerees par Django ; la table des categories de depenses est exclue a votre demande.
