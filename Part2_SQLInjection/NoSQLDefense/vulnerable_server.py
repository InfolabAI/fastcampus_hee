#!/usr/bin/env python3
"""
===========================================
 MCP  - SQL Injection  
===========================================

  :
     SQL Injection   .
        !

  :
1. SQL Injection  
2.    
3.      
4.    

 :
-   
-     
-     
"""

# ===========================================
#    
# ===========================================

import asyncio  #    
import sqlite3  # SQLite  /  
import json     # JSON     
from typing import Any  #    

# MCP (Model Context Protocol)  
# MCP AI      
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio


# ===========================================
#    
# ===========================================

def init_database():
    """
        

     :
    - SQLite  (vulnerable.db) 
    - users     
    -          

      :
    -     (SQL Injection  )
    -        !
    -  (bcrypt, argon2 )  
    """

    # vulnerable.db   (  )
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    # ==========================================
    #  users  
    # ==========================================
    # IF NOT EXISTS:     (  )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,        --    ID
            username TEXT NOT NULL,        --   ()
            password TEXT NOT NULL,        --  (,    !)
            email TEXT,                    --  ()
            role TEXT DEFAULT 'user',      --  (: 'user')
            credit_card TEXT               --   (  !)
        )
    ''')

    # ==========================================
    #     ( )
    # ==========================================
    #       
    cursor.execute("DELETE FROM users")

    # ==========================================
    #     
    # ==========================================
    # /   
    # (username, password, email, role, credit_card) 
    sample_users = [
        #   -   1
        ('admin', 'admin123', 'admin@example.com', 'admin', '1234-5678-9012-3456'),

        #    -   2~4
        ('alice', 'alice123', 'alice@example.com', 'user', '2345-6789-0123-4567'),
        ('bob', 'bob123', 'bob@example.com', 'user', '3456-7890-1234-5678'),
        ('charlie', 'charlie123', 'charlie@example.com', 'user', '4567-8901-2345-6789'),
    ]

    # ==========================================
    #      (Parameterized Query)
    # ==========================================
    #  :  ?  
    #  SQL Injection   !
    #
    #   : f"INSERT INTO users VALUES ('{username}', ...)"
    #   : "INSERT INTO users VALUES (?, ?, ...)", (username, ...)
    cursor.executemany(
        'INSERT INTO users (username, password, email, role, credit_card) VALUES (?, ?, ?, ?, ?)',
        sample_users
    )

    #   
    conn.commit()

    #   ( )
    conn.close()

    #    
    print("   ")
    print("  : admin, alice, bob, charlie")


# ===========================================
#  MCP   
# ===========================================
# "vulnerable-sql-server"  MCP  
server = Server("vulnerable-sql-server")


# ===========================================
#    (Tool)  
# ===========================================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    MCP       

     :
    -    4 () 
    -   , ,   
    -        

      :
    1. login:  
    2. search_user:  
    3. get_user_info:   
    4. update_email:  

       SQL Injection !
    """
    return [
        # ==========================================
        #   1:  (login)
        # ==========================================
        types.Tool(
            name="login",
            description="  (: SQL Injection )",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": " "
                    },
                    "password": {
                        "type": "string",
                        "description": ""
                    }
                },
                "required": ["username", "password"]  #  
            }
        ),

        # ==========================================
        #   2:   (search_user)
        # ==========================================
        types.Tool(
            name="search_user",
            description="  (: SQL Injection )",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "  "
                    }
                },
                "required": ["username"]
            }
        ),

        # ==========================================
        #   3:    (get_user_info)
        # ==========================================
        types.Tool(
            name="get_user_info",
            description=" ID   (: SQL Injection )",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",  #  string  (!)
                        "description": " ID"
                    }
                },
                "required": ["user_id"]
            }
        ),

        # ==========================================
        #   4:   (update_email)
        # ==========================================
        types.Tool(
            name="update_email",
            description="  (: SQL Injection )",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": " "
                    },
                    "new_email": {
                        "type": "string",
                        "description": "  "
                    }
                },
                "required": ["username", "new_email"]
            }
        )
    ]


# ===========================================
#    
# ===========================================

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
        

     :
    - name:    (: "login", "search_user")
    - arguments:    ( )

     :     SQL Injection  !

       :
    1.     
    2. f-string SQL    
    3.   SQL    

     :
    -  : username = "admin"
      → : SELECT * FROM users WHERE username='admin'

    -  : username = "admin' OR '1'='1"
      → : SELECT * FROM users WHERE username='admin' OR '1'='1'
      → :    !
    """

    # ==========================================
    #    ( )
    # ==========================================
    if not arguments:
        raise ValueError(" ")

    # ==========================================
    #   
    # ==========================================
    #     
    # (      )
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    try:
        # ==========================================
        #   : login
        # ==========================================
        if name == "login":
            """
              - SQL Injection  

              : 148 
             :    (  )

              :
            1.  : admin' OR '1'='1
            2.  : admin'--
            3. UNION : ' UNION SELECT ...
            """

            #    ( !)
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            # ==========================================
            #    !
            # ==========================================
            #   : f-string   
            #   (')     
            #
            #   :
            # username = "admin' OR '1'='1"
            # password = "anything"
            #
            #  :
            # SELECT * FROM users
            # WHERE username='admin' OR '1'='1' AND password='anything'
            #                         ↑   !
            #
            #   :
            # query = "SELECT * FROM users WHERE username=? AND password=?"
            # cursor.execute(query, (username, password))
            query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

            #    ( )
            print(f"  : {query}")

            #   (   !)
            cursor.execute(query)

            #    
            result = cursor.fetchone()

            if result:
                # ==========================================
                #    -   
                # ==========================================
                # result : (id, username, password, email, role, credit_card)
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[3],
                    'role': result[4]
                    #  : credit_card(result[5])  
                    #  SQL Injection   !
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"  !\n : {json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                # ==========================================
                #   
                # ==========================================
                return [
                    types.TextContent(
                        type="text",
                        text="  :      "
                    )
                ]

        # ==========================================
        #   : search_user
        # ==========================================
        elif name == "search_user":
            """
               - SQL Injection  

              : 180 
             : 🟠  (  )

              :
            1.   : %' OR '1'='1
            2.   : ' UNION SELECT credit_card, ...
            3.   : ' UNION SELECT * FROM sqlite_master--
            """

            #    
            username = arguments.get("username", "")

            # ==========================================
            #    !
            # ==========================================
            # LIKE  SQL Injection 
            #
            #    1:   
            # username = "%' OR '1'='1"
            # : SELECT ... WHERE username LIKE '%%' OR '1'='1%'
            #
            #    2: UNION 
            # username = "' UNION SELECT id, username, credit_card, 'hacked' FROM users--"
            # :     !
            query = f"SELECT id, username, email, role FROM users WHERE username LIKE '%{username}%'"

            print(f"  : {query}")

            cursor.execute(query)
            results = cursor.fetchall()  #   

            if results:
                #   
                users = [
                    {
                        'id': row[0],
                        'username': row[1],
                        'email': row[2],
                        'role': row[3]
                    }
                    for row in results
                ]
                return [
                    types.TextContent(
                        type="text",
                        text=f"   ({len(users)}):\n{json.dumps(users, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="   "
                    )
                ]

        # ==========================================
        #   : get_user_info
        # ==========================================
        elif name == "get_user_info":
            """
                - SQL Injection  

              : 215 
             : 🟠  (  )

              :
            -   SQL Injection   !
            -     (WHERE id=1 OR 1=1)

              :
            1.   : 1 OR 1=1
            2. UNION : 1 UNION SELECT credit_card, username, email, role FROM users
            3.   : 1 UNION SELECT sql, name, '', '' FROM sqlite_master
            """

            #  ID  (  - !)
            user_id = arguments.get("user_id", "")

            # ==========================================
            #    !
            # ==========================================
            #       
            #
            #    1:   
            # user_id = "1 OR 1=1"
            # : SELECT ... WHERE id=1 OR 1=1
            #       (OR 1=1     )
            #
            #    2: UNION  (  )
            # user_id = "1 UNION SELECT id, username, credit_card, role FROM users"
            # :    +    
            #
            #   :
            # query = "SELECT ... WHERE id=?"
            # cursor.execute(query, (user_id,))
            query = f"SELECT id, username, email, role FROM users WHERE id={user_id}"

            print(f"  : {query}")

            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'role': result[3]
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"  :\n{json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="    "
                    )
                ]

        # ==========================================
        #   : update_email
        # ==========================================
        elif name == "update_email":
            """
               - SQL Injection  

              : 248 
             :    (  )

              :
            - UPDATE  SQL Injection 
            -     
            -    

              :
            1.    : alice', email='hacked@evil.com' WHERE '1'='1
            2.   : alice', role='admin' WHERE username='alice
            3.   : alice', role='admin', credit_card='stolen' WHERE username='alice
            """

            #  
            username = arguments.get("username", "")
            new_email = arguments.get("new_email", "")

            # ==========================================
            #    !
            # ==========================================
            # UPDATE   
            #
            #    1:   (  → )
            # username = "alice"
            # new_email = "alice@example.com', role='admin' WHERE username='alice'--"
            #
            #  :
            # UPDATE users SET email='alice@example.com', role='admin'
            # WHERE username='alice'--' WHERE username='alice'
            #                        ↑  
            # → alice  admin !
            #
            #    2:    
            # username = "alice' OR '1'='1"
            # new_email = "hacked@evil.com"
            #
            # :    !
            #
            #   :
            # query = "UPDATE users SET email=? WHERE username=?"
            # cursor.execute(query, (new_email, username))
            query = f"UPDATE users SET email='{new_email}' WHERE username='{username}'"

            print(f"  : {query}")

            cursor.execute(query)
            conn.commit()  #   

            # rowcount:   
            if cursor.rowcount > 0:
                return [
                    types.TextContent(
                        type="text",
                        text=f"   ({cursor.rowcount}  )"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="    "
                    )
                ]

        # ==========================================
        #     
        # ==========================================
        else:
            raise ValueError(f"   : {name}")

    # ==========================================
    #   
    # ==========================================
    except sqlite3.Error as e:
        """
          

           !
        -      
        -  , ,     

            :
        1.    (MySQL, PostgreSQL, SQLite )
        2.   
        3.    

          :
        -   : " "
        -     
        -      
        """
        return [
            types.TextContent(
                type="text",
                text=f"  : {str(e)}\n      !"
            )
        ]
    finally:
        # ==========================================
        #   
        # ==========================================
        #     
        # (  ,     )
        conn.close()


# ===========================================
#    -  
# ===========================================

async def main():
    """
    MCP    

      :
    1.  
    2. stdio( )  MCP  
    3.   

     stdio :
    - MCP  (stdin/stdout)  
    - JSON-RPC  
    -      
    """

    # ==========================================
    #   
    # ==========================================
    init_database()

    # ==========================================
    #  MCP  
    # ==========================================
    # stdio_server()  :
    # - read_stream:   
    # - write_stream:   
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        #    
        print("   SQL   (SQL Injection  )")
        print("     !")

        #   (   )
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vulnerable-sql-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# ===========================================
#   
# ===========================================
if __name__ == "__main__":
    """
         
    (import   )

    asyncio.run():      
    """
    asyncio.run(main())


# ===========================================
#   
# ===========================================
"""
    :

1⃣ SQL Injection?
   -   SQL     
   -   SQL    

2⃣  :
    f"SELECT * FROM users WHERE username='{username}'"
    f"UPDATE users SET email='{email}' WHERE id={id}"

3⃣  :
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    cursor.execute("UPDATE users SET email=? WHERE id=?", (email, id))

4⃣  :
   -  : ' OR '1'='1
   -  : admin'--
   - UNION : ' UNION SELECT ...
   -  : ', role='admin' WHERE '1'='1

5⃣  :
     Parameterized Query 
       ( )
       (DB   )
       
      

  :
- test_vulnerable_server.py:   
- attack_simulation.py:   
- secure_server.py:   
"""
