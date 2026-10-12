#include <array>
#include <cctype>
#include <iostream>
#include <queue>
#include <stack>
#include <string>
#include <unordered_map>
#include <vector>
#include <sstream>

using namespace std;

// Smart Parking C++ backend for the Tkinter GUI.
// Communication protocol: one command per line, one response per line.
// Commands: STATUS, LIST, ADD|number|owner|type, EXIT|number, SEARCH|number,
//           QUEUE, STACK, STATS, QUIT
// Keep stdout reserved for protocol responses; diagnostics go to cerr.

constexpr int SLOT_COUNT = 20;

struct Vehicle {
    string number;
    string owner;
    string type;
    int slotIndex = -1;
};

static string normalizeNumber(const string& input) {
    string out;
    for (unsigned char ch : input) {
        if (!isspace(ch)) out += static_cast<char>(toupper(ch));
    }
    return out;
}

static vector<string> split(const string& input, char delimiter) {
    vector<string> result;
    string part;
    stringstream ss(input);
    while (getline(ss, part, delimiter)) result.push_back(part);
    return result;
}

static string cleanField(string value) {
    for (char& ch : value) {
        if (ch == '|' || ch == '\n' || ch == '\r' || ch == '\t') ch = ' ';
    }
    return value;
}

class SmartParking {
    array<bool, SLOT_COUNT> occupied{};
    vector<Vehicle> parked;
    queue<Vehicle> waiting;
    stack<int> vacated;
    unordered_map<string, size_t> indexByNumber;

    int freeSlot() const {
        if (!vacated.empty()) {
            int i = vacated.top();
            if (i >= 0 && i < SLOT_COUNT && !occupied[static_cast<size_t>(i)]) return i;
        }
        for (int i = 0; i < SLOT_COUNT; ++i)
            if (!occupied[static_cast<size_t>(i)]) return i;
        return -1;
    }

    bool isWaiting(const string& number) const {
        queue<Vehicle> copy = waiting;
        while (!copy.empty()) {
            if (copy.front().number == number) return true;
            copy.pop();
        }
        return false;
    }

    void rebuildIndex() {
        indexByNumber.clear();
        for (size_t i = 0; i < parked.size(); ++i) indexByNumber[parked[i].number] = i;
    }

    void removeParkedAt(size_t i) {
        parked.erase(parked.begin() + static_cast<vector<Vehicle>::difference_type>(i));
        rebuildIndex();
    }

    string slotName(int index) const {
        if (index < 0) return "WAITING";
        ostringstream out;
        out << 'P';
        if (index + 1 < 10) out << '0';
        out << index + 1;
        return out.str();
    }

public:
    string status() const {
        int count = 0;
        for (bool value : occupied) if (value) ++count;
        return "STATUS|" + to_string(SLOT_COUNT) + "|" + to_string(count) + "|" +
               to_string(SLOT_COUNT - count);
    }

    string list() const {
        // LIST|number,owner,type,slot;number,owner,type,slot
        string out = "LIST|";
        for (size_t i = 0; i < parked.size(); ++i) {
            if (i) out += ';';
            const auto& v = parked[i];
            out += v.number + "," + cleanField(v.owner) + "," + cleanField(v.type) +
                   "," + slotName(v.slotIndex);
        }
        return out;
    }

    string add(string number, string owner, string type) {
        number = normalizeNumber(number);
        owner = cleanField(owner);
        type = cleanField(type);
        if (number.empty() || owner.empty() || type.empty()) return "ERR|Please fill in all fields.";
        if (indexByNumber.count(number) || isWaiting(number))
            return "ERR|This registration number is already in the system.";

        int slot = freeSlot();
        if (slot < 0) {
            waiting.push({number, owner, type, -1});
            return "OK|Parking is full. Vehicle added to the FIFO waiting queue.";
        }

        if (!vacated.empty() && vacated.top() == slot) vacated.pop();
        occupied[static_cast<size_t>(slot)] = true;
        Vehicle v{number, owner, type, slot};
        indexByNumber[number] = parked.size();
        parked.push_back(v);
        return "OK|Vehicle registered successfully in slot " + slotName(slot) + ".";
    }

    string exitVehicle(string number) {
        number = normalizeNumber(number);
        auto found = indexByNumber.find(number);
        if (found == indexByNumber.end()) return "ERR|Vehicle is not currently parked.";

        size_t i = found->second;
        int slot = parked[i].slotIndex;
        occupied[static_cast<size_t>(slot)] = false;
        removeParkedAt(i);

        string message = "Vehicle exited from slot " + slotName(slot) + ".";
        if (!waiting.empty()) {
            Vehicle next = waiting.front();
            waiting.pop();
            next.slotIndex = slot;
            occupied[static_cast<size_t>(slot)] = true;
            indexByNumber[next.number] = parked.size();
            parked.push_back(next);
            message += " Waiting vehicle " + next.number + " was assigned the freed slot.";
        } else {
            vacated.push(slot);
            message += " Slot added to the recently-vacated stack.";
        }
        return "OK|" + message;
    }

    string search(string number) const {
        number = normalizeNumber(number);
        auto it = indexByNumber.find(number);
        if (it == indexByNumber.end()) return "ERR|Vehicle not found in parked vehicles.";

        const Vehicle& v = parked[it->second];
        return "FOUND|" + v.number + "|" + cleanField(v.owner) + "|" +
               cleanField(v.type) + "|" + slotName(v.slotIndex);
    }

    string queueView() const {
        string out = "QUEUE|";
        queue<Vehicle> copy = waiting;
        bool first = true;
        while (!copy.empty()) {
            if (!first) out += ';';
            first = false;
            const auto& v = copy.front();
            out += v.number + "," + cleanField(v.owner) + "," + cleanField(v.type);
            copy.pop();
        }
        return out;
    }

    string stackView() const {
        string out = "STACK|";
        stack<int> copy = vacated;
        bool first = true;
        while (!copy.empty()) {
            if (!first) out += ';';
            first = false;
            out += slotName(copy.top());
            copy.pop();
        }
        return out;
    }

    string stats() const {
        return "STATS|" + to_string(parked.size()) + "|" +
               to_string(waiting.size()) + "|" + to_string(vacated.size()) + "|" +
               to_string(indexByNumber.size());
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    SmartParking parking;
    string line;

    while (getline(cin, line)) {
        if (line == "QUIT") {
            cout << "BYE" << endl;
            break;
        }

        auto parts = split(line, '|');
        if (parts.empty()) {
            cout << "ERR|Empty command" << endl;
            continue;
        }

        string response;
        if (parts[0] == "STATUS") response = parking.status();
        else if (parts[0] == "LIST") response = parking.list();
        else if (parts[0] == "QUEUE") response = parking.queueView();
        else if (parts[0] == "STACK") response = parking.stackView();
        else if (parts[0] == "STATS") response = parking.stats();
        else if (parts[0] == "ADD" && parts.size() == 4)
            response = parking.add(parts[1], parts[2], parts[3]);
        else if (parts[0] == "EXIT" && parts.size() == 2)
            response = parking.exitVehicle(parts[1]);
        else if (parts[0] == "SEARCH" && parts.size() == 2)
            response = parking.search(parts[1]);
        else response = "ERR|Unknown command or invalid arguments";

        cout << response << endl;
    }
    return 0;
}
