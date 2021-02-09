def find_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).all()
    if len(instance) == 1:
        return instance[0]
    elif len(instance) > 1:
        raise Exception('in helpers.py create_or_find: there are multiple records with that criteria')
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

def create_csv(column_names, data):
    input = [column_names] + data
    csvfile = io.StringIO()
    csvwriter = csv.writer(csvfile)
    for i in input:
        csvwriter.writerow(i)
    return csvfile