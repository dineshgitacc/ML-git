'''Import system modules'''
import logging
import psycopg2
import sys

""" Import Django libraries """
from django.conf import settings

'''Import application modules'''
from analysis_request.models import AnalysisRequest

# Get an instance of a logging
log = logging.getLogger(__name__)


class AnalysisConnectionController():

    def connect_to_database(self, param, request, analysis_request_id=0):
        try:
            if param:
                if str(param['type']).lower() == 'postgres':
                    return self.connect_to_postgres(param, request, analysis_request_id)
            else:
                raise "No parameter found to establish connection"
        except Exception as e:
            log.error(e)
            raise e
        return False

    def connect_to_postgres(self, connection, request, analysis_request_id=0):
        print("summarization coming for database connection to fetch the file")
        log.info("summarization coming for database connection to fetch the file")
        con = None
        return_dict = {
            'text_analysis_path': '',
            'sentiment_analysis_path': '',
            'predictive_analysis_path':'',
            'summarization_path':'',
        }
        try:
            con = psycopg2.connect(database=connection['database'], user=connection['username'],
                                   password=connection['password'], port=connection['port'],
                                   host=connection['hostname'])
            cur = con.cursor()

            query_param = ''
            # Adding category as class field
            # if request['category']:
            #     query_param += " , " + request['category'] + " as class"
            # else:
            #     query_param += " , null as class"
            #
            # # Adding resolution as solution field
            # if request['resolution']:
            #     query_param += " , " + request['resolution'] + " as solution"
            # else:
            #     query_param += " , null as solution"

            query = "SELECT {} as id,  {} as content{} FROM {}.{}". \
                format(
                str(connection['primary_id']),
                request['content'],
                query_param,
                connection['schema'],
                request['table_name']
            )
            if request.get("min_id") and request.get("max_id"):
                query += " WHERE {} BETWEEN {} AND {}". \
                    format(
                    str(connection['primary_id']),
                    request["min_id"],
                    request["max_id"]
                )

            # query="SELECT "+str(connection['primary_id'])+" as id, "+request['content']+" as content"+query_param+" FROM "+connection['schema']+'.'+request['table_name']

            log.info(query)
            outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)

            filename = str(analysis_request_id) + '_' + str(connection['database']) + '_' + str(
                connection['schema']) + '_' + str(request['table_name'])
            with open(settings.MEDIA_ROOT + "/upload_file/" + filename + ".csv", 'w') as f:
                cur.copy_expert(outputquery, f)

            return_dict['text_analysis_path'] = "media/upload_file/" + filename + ".csv"

            sentiment_query = ''
            if 'sentiment' in request['request_type'].lower():
                sentiment_query += "SELECT {} as id,  {} as content{} FROM {}.{}". \
                    format(
                    str(connection['primary_id']),
                    request['sentimental_content'],
                    query_param,
                    connection['schema'],
                    request['table_name']
                )

                if request.get("min_id") and request.get("max_id"):
                    sentiment_query += " WHERE {} BETWEEN {} AND {}". \
                        format(
                        str(connection['primary_id']),
                        request["min_id"],
                        request["max_id"]
                    )

                if sentiment_query:
                    outputquery_sentiment = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(sentiment_query)
                    sentiment_filename = str(analysis_request_id) + '_' + str(connection['database']) + '_' + str(
                        connection['schema']) + '_' + str(request['table_name']) + '_sentiment_analysis'
                    with open(settings.MEDIA_ROOT + "/upload_file/" + sentiment_filename + ".csv", 'w') as f:
                        cur.copy_expert(outputquery_sentiment, f)
                    return_dict['sentiment_analysis_path'] = "media/upload_file/" + sentiment_filename + ".csv"


            summarization_query = ''
            if 'summarization' in request['request_type'].lower():
                summarization_query += "SELECT {} as id,  {} as content{} FROM {}.{}". \
                    format(
                    str(connection['primary_id']),
                    request['summarization_content'],
                    query_param,
                    connection['schema'],
                    request['table_name']
                )

                if request.get("min_id") and request.get("max_id"):
                    summarization_query += " WHERE {} BETWEEN {} AND {}". \
                        format(
                        str(connection['primary_id']),
                        request["min_id"],
                        request["max_id"]
                    )

                if summarization_query:
                    outputquery_summarization = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(summarization_query)
                    summarization_filename = str(analysis_request_id) + '_' + str(connection['database']) + '_' + str(
                        connection['schema']) + '_' + str(request['table_name']) + '_summarization'
                    with open(settings.MEDIA_ROOT + "/upload_file/" + summarization_filename + ".csv", 'w') as f:
                        cur.copy_expert(outputquery_summarization, f)
                    return_dict['summarization_path'] = "media/upload_file/" + summarization_filename + ".csv"


            predictive_query= ''
            sql_kw = ['table','from']
            predictive_col = request['predictive_content']
            for key_ in sql_kw:
                predictive_col = predictive_col.replace(key_,'"{}"'.format(key_))
            if 'predictive' in request['request_type'].lower():
                predictive_query += "SELECT {} as id,  {},{} ,'{}' as content{} FROM {}.{}". \
                    format(
                    str(connection['primary_id']),
                    predictive_col,
                    request['predictive_destination_coloumn'],
                    request['predictive_content'].split(',')[0],
                    query_param,
                    connection['schema'],
                    request['table_name']
                )
                log.info('predictive_query {}'.format(predictive_query))
                if request.get("min_id") and request.get("max_id"):
                    predictive_query += " WHERE {} BETWEEN {} AND {}". \
                        format(
                        str(connection['primary_id']),
                        request["min_id"],
                        request["max_id"]
                    )

                if predictive_query:
                    outputquery_predictive = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(predictive_query)
                    log.info('outputquery_predictive {}'.format(str(outputquery_predictive)))
                    predictive_filename = str(analysis_request_id) + '_' + str(connection['database']) + '_' + str(
                        connection['schema']) + '_' + str(request['table_name']) + '_predictive_analysis'
                    with open(settings.MEDIA_ROOT + "/upload_file/" + predictive_filename + ".csv", 'w') as f:
                        cur.copy_expert(outputquery_predictive, f)
                    return_dict['predictive_analysis_path'] = "media/upload_file/" + predictive_filename + ".csv"


            return return_dict

        except psycopg2.DatabaseError as e:
            log.error(e)
            raise e
        except Exception as e:
            log.error(e)
            raise e
        finally:
            if con:
                con.close()
        return False


