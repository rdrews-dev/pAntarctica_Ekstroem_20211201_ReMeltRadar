function query = escape_sql_string(query)
    query = regexprep(query, '([^\w])', '''||CHAR(${num2str(double($1))})||''');
end