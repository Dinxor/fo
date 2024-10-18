import aiosqlite


class DataBase:
    def __init__(self, path_to_db="files.db"):
        self.path_to_db = path_to_db

    async def execute(self, sql: str, parameters: tuple = None, fetchall=False, commit=False):
        async with aiosqlite.connect(self.path_to_db) as db:
            if not parameters:
                parameters = ()
            data = None
            cursor = await db.cursor()
            await cursor.execute(sql, parameters)

            if commit:
                await db.commit()

            if fetchall:
                data = await cursor.fetchall()
            return data

    async def create_table_files(self):
        sql = """
        CREATE TABLE IF NOT EXISTS files(
        id integer primary key,
        filename text,
        fileid integer)
        """
        await self.execute(sql=sql, commit=True)

    async def add_file_to_table(self, filename: str, fileid: int):
        sql = """
        INSERT INTO files(filename, fileid) VALUES (?,?)
        """

        await self.execute(
            sql=sql,
            parameters=(filename, fileid),
            commit=True
        )

    async def get_all_files(self):
        sql = """
        SELECT filename, fileid FROM files
        """
        return await self.execute(sql=sql, fetchall=True)
