## Benchmarks

This document presents comparison of performance between Latte and other
benchmarking tools.

### Software
* Latte version: 0.10.0
* NoSQLBench version: 4.15.66
* DataStax fork of Apache Cassandra version 4.0.1-SNAPSHOT, single local node, default settings
* Ubuntu 21.10, kernel 5.13.0-22-generic

### Hardware
* Intel Intel(R) Xeon(R) CPU E3-1505M v6 @ 3.00GHz  (4 cores)
* Turbo boost: disabled
* Hyperthreading: enabled
* Memory: 32 GB

### Task
Insert 10 million rows to an empty single-column table in Cassandra 4.0.1.

Schema:
```
CREATE KEYSPACE latte WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
CREATE TABLE latte.basic(id bigint PRIMARY KEY);
```

Latte workload (`write.rn`):
```rust
const INSERT = "insert";
const KEYSPACE = "latte";
const TABLE = "basic";

pub async fn prepare(db) {
    db.prepare(INSERT, `INSERT INTO ${KEYSPACE}.${TABLE}(id) VALUES (:id)`).await?;
}

pub async fn run(db, i) {
    db.execute_prepared(INSERT, [i]).await?
}
```

NoSQLBench workload (`write.yaml`):
```yaml
scenarios:
  default:
    run: run driver=cql cqldriver=oss protocol_version=v4 tags==phase:run threads==256 cycles==10000000
blocks:
  - tags:
      phase: run
    params:
      prepared: true
    statements:
      - insert: insert into latte.basic(id) values ({cycle});
        bindings:
          cycle: Identity()
```

Cassandra Stress workload (`stress-write.yaml`):
```yaml
keyspace: latte
table: basic

columnspec:
  - name: id
    size: SEQ(0..10000000)

insert:
  partitions: fixed(1)
  batchtype: UNLOGGED

queries:
  read:
     cql: select * from latte.basic where id = ?
     fields: samerow
```

Commands:
```
latte run write.rn -p 256 -d 10000000
nb --log-histostats hdr_stats.csv write.yaml
cassandra-stress user profile=stress-write.yaml n=10000000 no-warmup ops\(insert=1,read=0\) -rate threads=256
```
The commands were timed with `/usr/bin/time -v`.

### Results

&nbsp;                  |    Latte    |   NoSQLBench   |  Cassandra Stress    
------------------------|------------:|---------------:|------------------:
Threads                 |       1     |        256     |        256                 
Wall clock time         |   71.69 s   |     231.98 s   |     128.78 s           
CPU time (total)        |   64.54 s   |     784.63 s   |     364.20 s           
CPU time (user)         |   61.80 s   |     711.58 s   |     253.30 s           
CPU time (system)       |    2.74 s   |      73.05 s   |     110.90 s           
Peak memory             |    12.5 MB  |      893.7 MB  |    2,657.7 MB          
Major page faults       |       0     |        532     |         67               
Minor page faults       |   2,885     |    245,721     |    691,681           
Context switches        |  30,819     | 10,370,305     | 14,172,252          
