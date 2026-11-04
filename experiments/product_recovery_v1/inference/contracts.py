"""Strict observable-only boundary. No generator/template/truth imports."""
DOC={'source_id','company_id','text','source_type','document_kind','published_at','available_at','retrieved_at','valid_from_claimed','valid_to_claimed','provenance_status','document_family_id','origin_reference','publisher_description'}
TOP={'schema_version','company_id','snapshot_id','as_of','documents','mentions','claims','contradiction_records'}
def validate_inputs(view,contacts):
 if type(view) is not dict or set(view)!=TOP or view['schema_version']!='orglens-v4-source-observable.1':raise ValueError('Observable source envelope required')
 if any(view[k] for k in ['mentions','claims','contradiction_records']):raise ValueError('Only frozen raw source input supported')
 ids=set()
 for d in view['documents']:
  if type(d) is not dict or set(d)!=DOC or d['company_id']!=view['company_id'] or d['source_id'] in ids:raise ValueError('Invalid document boundary')
  if type(d['text']) is not str:raise ValueError('Source text required')
  ids.add(d['source_id'])
 if type(contacts) is not list:raise ValueError('Observable contacts required')
 seen=set()
 for c in contacts:
  if type(c) is not dict or set(c)!={'employee_id','display_name','title'} or any(type(x) is not str for x in c.values()) or c['employee_id'] in seen:raise ValueError('Invalid contact boundary')
  seen.add(c['employee_id'])
 return True
