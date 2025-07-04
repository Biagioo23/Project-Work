SELECT idalunno,
       cognome,
       nome,
       cf,
       datanascita,
       sesso,
       email,
       votodiploma,
       alunnoattivo,
       ritiratocorso,
       idcorsoanno,
       codicecorso,
       corso,
       votopagella,
       credito,
       votoammissioneesame,
       esitofinale
FROM public.iscrizioni
LIMIT 1000;