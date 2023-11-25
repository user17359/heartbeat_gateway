class Connection:
    encoded_name = ""

    def get_df_header(self, unit):
        pass

    async def start_connection(self, df, state, client, service, units):
        pass

    async def stop_connection(self, client):
        pass
