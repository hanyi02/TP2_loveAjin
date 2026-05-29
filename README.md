# LOVE LOG: DB 기반 인터랙티브 연애 시뮬레이션

## 프로젝트 소개

**LOVE LOG**는 Ren'Py 기반 연애 시뮬레이션 게임과 Flask API 서버, MariaDB를 연동한 DB 기반 인터랙티브 콘텐츠 프로젝트입니다.

사용자는 10일 동안 하루 2번 행동을 선택하며, 선택에 따라 매력, 지능, 스트레스, 남자 캐릭터별 호감도가 변화합니다. 특정 남주의 호감도가 100 이상이면 해당 남주의 해피엔딩으로 진입합니다.

본 프로젝트의 핵심은 게임 플레이 데이터가 단순히 게임 내부에서만 처리되는 것이 아니라, Flask API 서버를 거쳐 MariaDB에 저장된다는 점입니다. 저장된 데이터는 이후 사용자 행동 패턴, 캐릭터 선호도, 엔딩 분포, 최종 스탯 분석 등에 활용할 수 있습니다.

---

## 주요 기능

* Ren'Py 기반 선택형 연애 시뮬레이션 게임
* 플레이어 이름 입력 기능
* 입력한 이름을 게임 대사와 DB 저장 데이터에 반영
* 하루 2회 행동 선택 구조
* 남주별 대화 및 호감도 변화
* 매력, 지능, 스트레스, 돈 등 스탯 관리
* 해피엔딩, 노멀엔딩, 배드엔딩 분기
* Flask API 서버를 통한 MariaDB 저장
* 같은 와이파이 환경에서 다중 사용자 접속 가능
* 플레이어별 save_id 자동 발급
* 행동 로그, 호감도, 엔딩 결과 저장
* 추후 플레이 데이터 분석 가능

---

## 사용 기술

| 구분              | 기술              |
| --------------- | --------------- |
| Game Client     | Ren'Py          |
| Backend Server  | Python Flask    |
| Database        | MariaDB         |
| DB Tool         | HeidiSQL        |
| API 통신          | HTTP GET / POST |
| Version Control | Git / GitHub    |

---

## 시스템 구조

```text
Ren'Py 게임 클라이언트
        ↓
Flask API 서버
        ↓
MariaDB
```

Ren'Py 게임은 MariaDB에 직접 접속하지 않습니다.
게임에서 발생한 플레이 데이터는 Flask 서버로 HTTP 요청을 통해 전송되고, Flask 서버가 MariaDB에 데이터를 저장합니다.

이 구조는 클라이언트가 DB에 직접 접근하지 않고 서버를 통해 데이터를 처리하는 방식으로, 실제 서비스 구조와 유사합니다.

---

## API 구조

| Method | URL                   | 역할             |
| ------ | --------------------- | -------------- |
| GET    | `/api/test`           | Flask 서버 실행 확인 |
| GET    | `/api/characters`     | 캐릭터 정보 조회      |
| GET    | `/api/load/<save_id>` | 특정 저장 데이터 조회   |
| POST   | `/api/save_day`       | 하루 플레이 데이터 저장  |
| POST   | `/api/save_ending`    | 최종 엔딩 결과 저장    |

### GET과 POST의 역할

* **GET**: 서버에서 데이터를 조회할 때 사용
* **POST**: 게임 데이터를 서버로 보내 저장할 때 사용

예시:

```text
GET /api/characters
→ MariaDB의 male_character 테이블에서 캐릭터 정보를 조회

POST /api/save_day
→ 하루 종료 시 플레이어 상태, 호감도, 행동 로그 저장

POST /api/save_ending
→ 엔딩 도달 시 최종 엔딩 결과 저장
```

---

## 데이터베이스 구조

DB 이름:

```sql
love_ajin
```

사용 테이블:

| 테이블명             | 역할                    |
| ---------------- | --------------------- |
| `male_character` | 남자 캐릭터 기본 정보 저장       |
| `player_save`    | 플레이어 이름, 날짜, 돈, 스탯 저장 |
| `affection_save` | 남주별 호감도 저장            |
| `inventory_save` | 아이템 보유 정보 저장          |
| `action_log`     | 사용자가 선택한 행동 로그 저장     |
| `ending_log`     | 최종 엔딩 결과 저장           |

---

## 테이블 설명

### 1. `male_character`

남자 캐릭터의 기본 정보를 저장합니다.

저장 정보:

* male_id
* male_name
* male_title
* base_image
* reaction_image_1
* reaction_image_2
* happy_ending_image

---

### 2. `player_save`

플레이어의 현재 상태를 저장합니다.

저장 정보:

* save_id
* player_name
* current_day
* gold
* hp
* charm
* intelligence
* stress
* created_at
* updated_at

---

### 3. `affection_save`

남자 캐릭터별 호감도를 저장합니다.

저장 정보:

* save_id
* male_id
* affection

DB 내부에서는 `male_id`로 저장되지만, 조회 시 `male_character` 테이블과 JOIN하여 캐릭터 이름으로 확인할 수 있습니다.

---

### 4. `inventory_save`

플레이어가 구매한 아이템 정보를 저장합니다.

저장 정보:

* save_id
* item_id
* item_count

---

### 5. `action_log`

사용자가 선택한 행동 기록을 저장합니다.

예시:

```text
하원준 대화 - 일정 플러팅
폭풍 업무
휴식
상점 구매
```

이 테이블은 추후 사용자 행동 패턴 분석에 활용할 수 있습니다.

---

### 6. `ending_log`

최종 엔딩 결과를 저장합니다.

저장 정보:

* ending_id
* best_male_id
* highest_score
* final_charm
* final_intelligence
* final_stress

---

## 프로젝트 폴더 구조

```text
love_Ajin/
├─ flask_server/
│  └─ app.py
│
├─ game/
│  ├─ script.rpy
│  ├─ options.rpy
│  ├─ screens.rpy
│  ├─ images/
│  ├─ gui/
│  └─ audio/
│
├─ project.json
└─ README.md
```

---

## 실행 방법

## 1. MariaDB 실행

MariaDB 또는 HeidiSQL을 실행합니다.

DB 이름은 다음과 같습니다.

```sql
love_ajin
```

DB가 없다면 SQL 파일을 실행하여 테이블을 생성합니다.

---

## 2. Flask 서버 실행

터미널 또는 PowerShell에서 다음 명령어를 실행합니다.

```powershell
cd C:\love_Ajin\flask_server
python app.py
```

정상 실행 시 다음과 같은 로그가 출력됩니다.

```text
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://10.2.13.61:5000
```

의미:

```text
127.0.0.1:5000
→ 현재 PC 내부에서 접속하는 주소

10.2.13.61:5000
→ 같은 와이파이에 연결된 다른 PC에서 접속할 수 있는 주소

0.0.0.0
→ 외부 접속도 받을 수 있도록 서버를 연 상태
```

---

## 3. Flask 서버 확인

브라우저에서 다음 주소로 접속합니다.

```text
http://10.2.13.61:5000/api/characters
```

캐릭터 정보가 JSON 형태로 출력되면 Flask 서버와 MariaDB 연결이 정상입니다.

---

## 4. Ren'Py 게임 실행

Ren'Py Launcher에서 프로젝트를 실행합니다.

게임 시작 시 플레이어 이름을 입력합니다.
입력한 이름은 게임 대사와 MariaDB의 `player_save` 테이블에 반영됩니다.

---

## 5. DB 저장 확인

게임에서 하루 행동 2번을 모두 완료하면 Flask 서버에 다음 로그가 출력됩니다.

```text
POST /api/save_day HTTP/1.1" 200
```

엔딩에 도달하면 다음 로그가 출력됩니다.

```text
POST /api/save_ending HTTP/1.1" 200
```

---

## 발표용 조회 SQL

### 플레이어 저장 정보 확인

```sql
USE love_ajin;

SELECT 
    save_id,
    player_name,
    current_day,
    gold,
    charm,
    intelligence,
    stress,
    updated_at
FROM player_save
ORDER BY save_id DESC;
```

---

### 남주별 호감도 확인

```sql
SELECT
    a.save_id,
    p.player_name,
    m.male_name AS 공략대상,
    a.affection AS 호감도
FROM affection_save a
JOIN player_save p
    ON a.save_id = p.save_id
JOIN male_character m
    ON a.male_id = m.male_id
ORDER BY a.save_id DESC, a.affection DESC;
```

---

### 행동 로그 확인

```sql
SELECT
    l.save_id,
    p.player_name,
    l.day,
    l.action_name,
    l.created_at
FROM action_log l
JOIN player_save p
    ON l.save_id = p.save_id
ORDER BY l.log_id DESC;
```

---

### 엔딩 결과 확인

```sql
SELECT
    e.ending_log_id,
    e.save_id,
    p.player_name,
    e.ending_id,
    m.male_name AS 최종공략대상,
    e.highest_score AS 최종호감도,
    e.final_charm AS 최종매력,
    e.final_intelligence AS 최종지능,
    e.final_stress AS 최종스트레스,
    e.created_at
FROM ending_log e
JOIN player_save p
    ON e.save_id = p.save_id
LEFT JOIN male_character m
    ON e.best_male_id = m.male_id
ORDER BY e.ending_log_id DESC;
```

---

## 시연 흐름

1. Flask 서버 실행 확인
2. `/api/characters` 접속으로 캐릭터 정보 조회 확인
3. Ren'Py 게임 실행
4. 플레이어 이름 입력
5. 남직원 대화 선택
6. 호감도 상승 확인
7. 업무 또는 휴식 선택
8. 하루 종료 후 Flask 로그 확인
9. MariaDB에서 `player_save`, `affection_save`, `action_log` 확인
10. 엔딩 도달 후 `ending_log` 확인

---

## 주요 시연 포인트

* Flask 서버가 같은 와이파이 환경에서 접속 가능함
* Ren'Py 게임이 직접 DB에 접속하지 않고 Flask 서버로 데이터를 전송함
* 하루 종료 시 `/api/save_day`로 POST 요청이 전송됨
* 플레이어 이름, 스탯, 호감도, 행동 로그가 DB에 저장됨
* 엔딩 도달 시 `/api/save_ending`으로 최종 결과가 저장됨
* 저장된 데이터는 추후 분석에 활용 가능함

---

## 추후 데이터 분석 방향

MariaDB에 누적된 플레이 데이터를 바탕으로 다음과 같은 분석이 가능합니다.

* 날짜별 공략 대상 분석
* 남주별 인기 순위 분석
* 해피엔딩 / 노멀엔딩 / 배드엔딩 비율 분석
* 엔딩별 평균 스탯 분석
* 사용자 행동 선택 빈도 분석
* 해피엔딩 유저와 배드엔딩 유저의 행동 패턴 비교
* 캐릭터별 최종 호감도 분포 분석

---

## 팀원 역할

### 인터랙티브 클라이언트 및 UX 플로우 개발

* Ren'Py 게임 클라이언트 구현
* 10일 진행 및 하루 2회 행동 선택 루프 설계
* 남주별 대화 및 선택지 분기 구현
* 호감도, 매력, 지능, 스트레스 변화 로직 구현
* 플레이어 이름 입력 및 대사 반영 기능 구현
* 캐릭터 이미지 자동 배치 및 화면 구성 개선
* 엔딩 분기 흐름 구현

---

### API 서버 및 데이터 파이프라인 구현

* Flask API 서버 구축
* Ren'Py와 MariaDB 사이 Bridge Server 구조 설계
* GET `/api/characters` 캐릭터 정보 조회 API 구현
* POST `/api/save_day` 하루 플레이 데이터 저장 API 구현
* POST `/api/save_ending` 엔딩 결과 저장 API 구현
* 같은 와이파이 기반 다중 사용자 접속 환경 구성
* 사용자별 save_id 자동 발급 및 저장 구조 개선
* Flask 서버 로그를 통한 API 요청 검증

---

### 데이터베이스 아키텍처 및 분석 설계

* MariaDB 테이블 6개 구조 설계
* 캐릭터, 플레이어, 호감도, 인벤토리, 행동 로그, 엔딩 로그 저장 구조 구성
* save_id, male_id 기반 관계형 데이터 구조 설계
* HeidiSQL을 활용한 데이터 저장 및 조회 검증
* JOIN 쿼리를 활용한 발표용 조회 화면 구성
* 플레이 로그 기반 데이터 분석 방향 기획
* 캐릭터 선호도, 엔딩 분포, 행동 패턴 분석 확장 아이디어 도출

---

## 프로젝트 의의

본 프로젝트는 단순한 연애 시뮬레이션 게임 구현을 넘어, 사용자의 선택 데이터를 수집하고 분석할 수 있는 구조를 구현한 DB 기반 인터랙티브 콘텐츠 시스템입니다.

Ren'Py 게임 클라이언트에서 발생한 플레이 데이터는 Flask API 서버를 거쳐 MariaDB에 저장되며, 저장된 데이터는 향후 캐릭터 선호도, 엔딩 분포, 행동 패턴 분석 등으로 확장할 수 있습니다.
