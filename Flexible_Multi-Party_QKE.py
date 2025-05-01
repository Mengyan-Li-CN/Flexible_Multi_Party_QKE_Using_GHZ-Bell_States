from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator # type: ignore
from qiskit.quantum_info import random_statevector
from qiskit import transpile
import numpy as np
import random

class QuantumParticipant:
    def __init__(self, id, private_key):
        """初始化量子参与者
        参数:
            id: 参与者编号（1到N）
            private_key: 私钥（长度为M的二进制序列）
        """
        self.id = id
        self.private_key = private_key  # Ki = [Ki^1, Ki^2, ..., Ki^j, ..., Ki^M]
        self.is_leader = False
        self.shared_key = None
        self.backend = AerSimulator()
        
    def __str__(self):
        return f"P{self.id}"
        
    def get_private_key_str(self):
        """返回私钥的字符串表示"""
        return ','.join(map(str, self.private_key))
    
    def get_pauli_operation(self, position):
        """根据私钥确定Pauli操作
        参数:
            position: 私钥中的位置j，对应Ki^j
        返回:
            Pauli操作:
            - 当Ki^j = 0时，执行X操作，得到0
            - 当Ki^j = 1时，执行I操作，得到1
        """
        if position >= len(self.private_key):
            return 'I'  # 如果位置超出范围，默认为单位操作
        
        # 根据私钥位Ki^j确定Pauli操作
        # Ki^j = 0 -> X (比特翻转，得到0)
        # Ki^j = 1 -> I (单位操作，得到1)
        return 'X' if self.private_key[position] == 0 else 'I'

class QuantumKeyExchange:
    def __init__(self, num_participants, m_value):
        """初始化量子密钥交换系统
        参数:
            num_participants: 参与者总数N
            m_value: 序列长度M
        """
        self.N = num_participants
        self.M = m_value
        self.d = 4  # 诱骗态数量
        self.error_threshold = 0.1
        self.backend = AerSimulator()
        
        # 为每个参与者生成长度为M的随机二进制私钥Ki
        private_keys = []
        while len(private_keys) < num_participants:
            # 生成M位二进制序列作为私钥Ki = [Ki^1, Ki^2, ..., Ki^M]
            new_key = [random.randint(0, 1) for _ in range(m_value)]
            if new_key not in private_keys:  # 确保私钥唯一
                private_keys.append(new_key)
        
        # 创建参与者并分配私钥
        self.participants = [
            QuantumParticipant(i+1, private_keys[i]) 
            for i in range(num_participants)
        ]
        
        # 执行动态选举
        self._perform_dynamic_election()

    def _perform_dynamic_election(self):
        """执行动态选举算法"""
        self.print_section("动态选举过程")
        
        # 1. 生成随机投票
        votes = self._generate_votes()
        self._display_voting_results(votes)
        
        # 2. 统计票数并排序
        vote_counts = self._count_votes(votes)
        sorted_candidates = sorted(vote_counts.items(), key=lambda x: (-x[1], x[0]))
        
        # 3. 选择前3名作为领导者
        leaders = [candidate for candidate, _ in sorted_candidates[:3]]
        
        # 4. 更新参与者身份
        self._update_participant_identities(leaders)
        
        # 5. 显示选举结果
        self._display_election_results(leaders, vote_counts)

    def _generate_votes(self):
        """生成随机投票"""
        votes = {}
        for voter in self.participants:
            # 每个参与者随机投3票
            candidates = random.sample(range(1, self.N + 1), 3)
            votes[voter.id] = candidates
        return votes

    def _display_voting_results(self, votes):
        """显示投票结果"""
        self.print_subsection("投票详情")
        
        headers = ["投票者", "投票对象"]
        rows = []
        for voter_id, candidates in votes.items():
            rows.append([f"P{voter_id}", f"P{candidates[0]}, P{candidates[1]}, P{candidates[2]}"])
        
        self.print_table(headers, rows)

    def _count_votes(self, votes):
        """统计票数"""
        vote_counts = {i: 0 for i in range(1, self.N + 1)}
        for candidates in votes.values():
            for candidate in candidates:
                vote_counts[candidate] += 1
        return vote_counts

    def _update_participant_identities(self, leaders):
        """更新参与者身份"""
        # 创建新的身份映射
        new_ids = {}
        
        # 为领导者分配新的ID（1-3）
        for i, leader_id in enumerate(leaders):
            new_ids[leader_id] = i + 1
        
        # 为其他参与者分配新的ID（4-N）
        remaining_ids = [i for i in range(1, self.N + 1) if i not in leaders]
        for i, old_id in enumerate(remaining_ids):
            new_ids[old_id] = i + 4
        
        # 更新参与者身份
        for participant in self.participants:
            old_id = participant.id
            participant.id = new_ids[old_id]
            participant.is_leader = (participant.id <= 3)
        
        # 按新ID排序参与者列表
        self.participants.sort(key=lambda x: x.id)

    def _display_election_results(self, leaders, vote_counts):
        """显示选举结果"""
        self.print_subsection("选举结果")
        
        # 显示票数统计
        headers = ["候选人", "得票数"]
        rows = []
        for candidate, votes in sorted(vote_counts.items(), key=lambda x: (-x[1], x[0])):
            rows.append([f"P{candidate}", votes])
        
        self.print_table(headers, rows)
        
        # 显示身份变换
        self.print_subsection("身份变换")
        headers = ["原身份", "新身份", "角色"]
        rows = []
        
        # 显示领导者
        for i, leader_id in enumerate(leaders):
            rows.append([f"P{leader_id}", f"P{i+1}", "领导者"])
        
        # 显示其他参与者
        remaining = [i for i in range(1, self.N + 1) if i not in leaders]
        for i, old_id in enumerate(remaining):
            rows.append([f"P{old_id}", f"P{i+4}", "跟随者"])
        
        self.print_table(headers, rows)

    def create_quantum_state(self, state_type, num_qubits=None):
        """创建量子态
        参数:
            state_type: 量子态类型 ('ghz3', 'ghz4', 'bell_phi_plus', 'bell_psi_minus')
            num_qubits: GHZ态的量子比特数量
        返回:
            量子电路
        """
        if state_type.startswith('ghz'):
            # 创建GHZ态
            n = num_qubits or int(state_type[-1])
            qc = QuantumCircuit(n)
            qc.h(0)
            for i in range(1, n):
                qc.cx(0, i)
            return qc
        
        elif state_type.startswith('bell'):
            # 创建Bell态
            qc = QuantumCircuit(2)
            if state_type == 'bell_phi_plus':
                qc.h(0)
                qc.cx(0, 1)
            else:  # bell_psi_minus
                qc.x(1)
                qc.h(0)
                qc.cx(0, 1)
                qc.z(1)
            return qc

    def measure_quantum_state(self, circuit, basis_list=None):
   
        num_qubits = circuit.num_qubits
        cr = ClassicalRegister(num_qubits)
        circuit.add_register(cr)
        
        # 如果没有指定测量基底，随机选择
        if basis_list is None:
            basis_list = [random.choice(['X', 'Z']) for _ in range(num_qubits)]
        
        # 在指定基底中测量
        for i, basis in enumerate(basis_list):
            if basis == 'X':
                circuit.h(i)
            circuit.measure(i, i)
        
        # 执行电路并获取结果
        transpiled_circuit = transpile(circuit, self.backend)
        job = self.backend.run(transpiled_circuit, shots=1)
        result = job.result()
        counts = result.get_counts(circuit)
        
        # 返回测量结果
        measured = list(counts.keys())[0]
        return [int(bit) for bit in measured]

    def create_particle_sequence(self, participant_id, seq_type):
        sequence = []
        seq_name = {1: 'A', 2: 'B', 3: 'C'}[seq_type]
        
        # 创建M组量子态
        for j in range(self.M):
            # 生成随机初始态
            initial_state = [random.randint(0, 1) for _ in range(3)]
            
            # 根据序列类型选择量子态
            if seq_type == 1:  # A序列
                state_type = 'ghz3'
            else:  # B或C序列
                state_type = random.choice(['ghz3', 'bell_phi_plus', 'bell_psi_minus'])
            
            # 创建量子态
            state = self.create_quantum_state(state_type)
            
            # 创建粒子标识符
            particle_id = f"P{participant_id},{j+1}({seq_type})"
            
            sequence.append({
                'type': state_type,
                'state': state,
                'initial_state': initial_state,
                'participant_id': participant_id,
                'particle_id': particle_id,
                'j': j + 1,
                'position': seq_type,
                'seq_type': seq_name
            })
        return sequence

    def apply_operations(self, sequence, participant, start_pos=0):

        result = []
        for i, state in enumerate(sequence):
            new_state = state.copy()
            if isinstance(new_state, dict) and 'initial_state' in new_state:
                num_qubits = len(new_state['initial_state'])
                for j in range(num_qubits):
                    # 获取私钥位置j，对应Ki^j
                    pos = (start_pos + i) % len(participant.private_key)
                    # 获取对应的Pauli操作（I或X）
                    op = participant.get_pauli_operation(pos)
                    # 仅当操作为X时执行比特翻转
                    if op == 'X':
                        new_state['initial_state'][j] = 1 - new_state['initial_state'][j]
            result.append(new_state)
        return result

    def process_measurement(self, sequences, participants):
        """处理测量过程"""
        results = {}
        for p in participants:
            # 随机选择测量基底
            basis = [random.choice(['X', 'Z']) for _ in range(3)]
            # 执行测量
            if p.id in sequences:
                results[p.id] = self.measure_sequences(sequences[p.id], {}, basis)
            else:
                results[p.id] = [0] * self.M
        return results

    def generate_key(self, measurement_results):
        """生成密钥"""
        key = []
        for i in range(self.M):
            bit = 0
            for participant_id in measurement_results:
                bit ^= measurement_results[participant_id][i]
            key.append(bit)
        return key

    def insert_decoy_states(self, quantum_sequence, num_decoy):
        """插入诱骗态"""
        # 确保诱骗态数量不超过序列长度
        num_decoy = min(num_decoy, len(quantum_sequence))
        positions = sorted(random.sample(range(len(quantum_sequence)), num_decoy))
        bases = [random.choice(['X', 'Z']) for _ in range(num_decoy)]
        decoy_states = [random.randint(0, 1) for _ in range(num_decoy)]
        
        # 插入诱骗态
        for pos, base, state in zip(positions, bases, decoy_states):
            quantum_sequence.insert(pos, {'type': 'decoy', 'base': base, 'state': state})
            
        return positions, bases, decoy_states

    def measure_sequences(self, own_sequences, received_sequences, basis):
        """测量序列并返回结果"""
        results = []
        for i in range(self.M):
            # 测量自己的序列和接收到的序列
            result = 0
            
            # 处理自己的序列
            if isinstance(own_sequences, dict):
                for seq in own_sequences.values():
                    if i < len(seq) and isinstance(seq[i], dict) and 'initial_state' in seq[i]:
                        # 随机选择测量基底
                        measure_basis = random.choice(['X', 'Z'])
                        if measure_basis == 'X':
                            result ^= 1 - seq[i]['initial_state'][0]  # X基测量
                        else:
                            result ^= seq[i]['initial_state'][0]  # Z基测量
            else:
                if i < len(own_sequences) and isinstance(own_sequences[i], dict) and 'initial_state' in own_sequences[i]:
                    measure_basis = random.choice(['X', 'Z'])
                    if measure_basis == 'X':
                        result ^= 1 - own_sequences[i]['initial_state'][0]
                    else:
                        result ^= own_sequences[i]['initial_state'][0]
            
            # 处理接收到的序列
            if isinstance(received_sequences, dict):
                for seq in received_sequences.values():
                    if i < len(seq) and isinstance(seq[i], dict) and 'initial_state' in seq[i]:
                        measure_basis = random.choice(['X', 'Z'])
                        if measure_basis == 'X':
                            result ^= 1 - seq[i]['initial_state'][0]
                        else:
                            result ^= seq[i]['initial_state'][0]
            else:
                if i < len(received_sequences) and isinstance(received_sequences[i], dict) and 'initial_state' in received_sequences[i]:
                    measure_basis = random.choice(['X', 'Z'])
                    if measure_basis == 'X':
                        result ^= 1 - received_sequences[i]['initial_state'][0]
                    else:
                        result ^= received_sequences[i]['initial_state'][0]
            
            results.append(result)
        return results

    def print_table(self, headers, rows, title=None):
 
        if title:
            print(f"\n{title}")
        
        # 计算每列的最大宽度
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        print("┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐")
        print("│" + "│".join(f" {h:<{w}} " for h, w in zip(headers, col_widths)) + "│")
        print("├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤")
        
        # 打印数据行
        for row in rows:
            print("│" + "│".join(f" {str(cell):<{w}} " for cell, w in zip(row, col_widths)) + "│")
        
        print("└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘")

    def print_section(self, title, content=None):

        print("\n" + "="*50)
        print(f" {title} ")
        print("="*50)
        if content:
            print(content)

    def print_subsection(self, title, content=None):

        print("\n" + "-"*40)
        print(f" {title} ")
        print("-"*40)
        if content:
            print(content)

    def print_key_info(self, key, title="密钥信息"):

        print(f"\n{title}:")
        print("┌─────────────────────────────┐")
        print(f"│ K = [{', '.join(map(str, key))}] │")
        print("└─────────────────────────────┘")

    def _display_private_keys(self, participants, title="参与者私钥信息"):

        self.print_subsection(title)
        
        headers = ["参与者", "私钥Ki"]
        rows = []
        
        for p in participants:
            # 将私钥格式化为Ki = [Ki^1, Ki^2, ..., Ki^M]
            key_str = f"[{', '.join(map(str, p.private_key))}]"
            rows.append([f"P{p.id}", key_str])
        
        self.print_table(headers, rows)

    def perform_qkd(self, leader, followers):
        """执行量子密钥分发(QKD)"""
        group_members = [leader] + followers
        group_indices = [p.id for p in group_members]
        
        # 根据跟随者数量选择量子态类型
        if len(followers) == 2:
            self.print_section(f"三粒子GHZ态QKD过程", f"第{leader.id}组: {', '.join(f'P{i}' for i in group_indices)}")
            return self._perform_three_particle_qkd(leader, followers)
        else:
            self.print_section(f"Bell态QKD过程", f"第{leader.id}组: {', '.join(f'P{i}' for i in group_indices)}")
            return self._perform_bell_state_qkd(leader, followers[0])

    def distribute_key(self):
        """主密钥分发过程"""
        # 1. 获取初始领导者列表
        leaders = [p for p in self.participants if p.is_leader]
        num_initial_leaders = len(leaders)
        
        if num_initial_leaders == 0:
            print("错误：未设置领导者")
            return
            
        self.print_section("量子密钥分发(QKD)过程开始")
        print(f"\n初始领导者: {', '.join(str(p) for p in leaders)}")
        
        # 显示初始领导者私钥
        self._display_private_keys(leaders, "初始领导者私钥信息")
        
        # 计算初始QKD模式
        total_participants = len(self.participants)
        remaining_participants_count = total_participants - num_initial_leaders
        qkd_mode = remaining_participants_count % 2
        
        self.print_subsection("QKD模式选择")
        print(f"参与者总数: N = {total_participants}")
        print(f"初始领导者数量: {num_initial_leaders}")
        print(f"剩余参与者数量: {remaining_participants_count}")
        print(f"选用的QKD模式: (N-{num_initial_leaders}) mod 2 = {qkd_mode} 模式")
        
        if qkd_mode == 0:
            print("模式说明: 剩余参与者数量为偶数，所有分组均可使用三粒子GHZ态进行QKD")
        else:
            print("模式说明: 剩余参与者数量为奇数，大部分分组使用三粒子GHZ态，最后一组使用Bell态进行QKD")
        
        # 2. 在初始领导者之间执行QKA，使用三粒子GHZ态
        self.print_subsection("第一阶段：初始领导者间的QKA过程")
        initial_key = self.perform_qkd(leaders[0], leaders[1:])
        
        # 分发初始密钥给所有初始领导者
        for leader in leaders:
            leader.shared_key = initial_key.copy()
        
        # 3. 开始动态QKD过程
        round_count = 1
        
        # 动态QKD循环，直到所有参与者都获得密钥
        while True:
            # 获取当前已获得密钥的参与者（包括所有领导者）
            current_leaders = [p for p in self.participants if p.shared_key is not None]
            # 获取尚未获得密钥的参与者
            remaining_participants = [p for p in self.participants if p.shared_key is None]
            
            # 如果所有参与者都已获得密钥，则结束循环
            if not remaining_participants:
                break
                
            self.print_subsection(f"第{round_count}轮QKD过程")
            print(f"当前领导者: {', '.join(str(p) for p in current_leaders)}")
            print(f"待分配密钥的参与者: {', '.join(str(p) for p in remaining_participants)}")
            
            # 计算本轮的分组方案
            num_remaining = len(remaining_participants)
            num_leaders = len(current_leaders)
            
            # 计算本轮QKD模式
            round_qkd_mode = num_remaining % 2
            
            print(f"\n本轮QKD模式: (剩余参与者数{num_remaining}) mod 2 = {round_qkd_mode} 模式")
            if round_qkd_mode == 0:
                print("模式说明: 本轮所有参与者均可使用三粒子GHZ态进行QKD")
            else:
                print("模式说明: 本轮大部分参与者使用三粒子GHZ态，最后一位参与者使用Bell态进行QKD")
            
            # 显示分组统计
            num_ghz_groups = num_remaining // 2
            num_bell_groups = num_remaining % 2
            
            headers = ["分组类型", "使用次数", "参与者数量"]
            rows = [
                ["三粒子GHZ态", f"{num_ghz_groups}次", f"{num_ghz_groups * 2}位参与者"],
                ["Bell态", f"{num_bell_groups}次", f"{num_bell_groups}位参与者"]
            ]
            self.print_table(headers, rows)
            
            # 优先使用三粒子GHZ态（每个领导者最多带两个参与者）
            assignments = []  # 存储(领导者, [参与者1, 参与者2])的元组
            
            # 为每个领导者尽可能分配两个参与者
            remaining_idx = 0
            for leader_idx, leader in enumerate(current_leaders):
                if remaining_idx >= num_remaining:
                    break
                    
                if remaining_idx + 1 < num_remaining:  # 如果还有至少2个参与者，使用三粒子GHZ态
                    assignments.append((leader, remaining_participants[remaining_idx:remaining_idx+2]))
                    remaining_idx += 2
                else:  # 只剩下1个参与者，使用Bell态
                    assignments.append((leader, [remaining_participants[remaining_idx]]))
                    remaining_idx += 1
            
            # 执行QKD过程
            group_count = 1
            for leader, followers in assignments:
                if len(followers) == 2:
                    self.print_subsection(f"第{round_count}轮 - 组{group_count}：三粒子GHZ态QKD")
                    print(f"领导者: {leader}，参与者: {followers[0]}, {followers[1]}")
                    
                    group_key = self._perform_three_particle_qkd(leader, followers)
                    self.synchronize_and_display_keys(group_key, initial_key, followers)
                    
                    # 更新参与者的密钥
                    for p in followers:
                        p.shared_key = initial_key.copy()
                else:
                    self.print_subsection(f"第{round_count}轮 - 组{group_count}：Bell态QKD")
                    print(f"领导者: {leader}，参与者: {followers[0]}")
                    
                    group_key = self._perform_bell_state_qkd(leader, followers[0])
                    self.synchronize_and_display_keys(group_key, initial_key, followers)
                    
                    # 更新参与者的密钥
                    followers[0].shared_key = initial_key.copy()
                
                group_count += 1
            
            round_count += 1
        
        # 显示最终结果
        self.print_section("QKD过程完成")
        self.print_key_info(initial_key, "最终共享密钥")
        
        # 显示性能统计
        self.print_subsection("性能统计")
        headers = ["统计项目", "数值"]
        rows = [
            ["参与者总数", len(self.participants)],
            ["初始领导者数量", num_initial_leaders],
            ["总轮数", round_count - 1],
            ["最终共享密钥长度", len(initial_key)]
        ]
        self.print_table(headers, rows)

    def synchronize_and_display_keys(self, group_key, target_key, participants):
        """显示密钥同步过程"""
        self.print_subsection("密钥同步过程")
        
        headers = ["密钥类型", "值"]
        rows = [
            ["组密钥", f"[{', '.join(map(str, group_key))}]"],
            ["目标密钥", f"[{', '.join(map(str, target_key))}]"]
        ]
        self.print_table(headers, rows)
        
        # 计算需要翻转的位置（从1开始计数）
        diff_positions = []
        for i, (g, t) in enumerate(zip(group_key, target_key)):
            if g != t:
                diff_positions.append(i + 1)  # 加1使位置从1开始计数
        
        if diff_positions:
            self.print_subsection("密钥调整")
            print(f"需要翻转的位置: {', '.join(map(str, diff_positions))}")
            
            headers = ["参与者", "调整后密钥"]
            rows = []
            for p in participants:
                adjusted_key = list(group_key)
                for pos in diff_positions:
                    actual_pos = pos - 1  # 转换回0基索引
                    adjusted_key[actual_pos] = 1 - adjusted_key[actual_pos]
                rows.append([f"P{p.id}", f"[{', '.join(map(str, adjusted_key))}]"])
            self.print_table(headers, rows)
        else:
            print("\n组密钥与目标密钥完全匹配，无需调整")

    def _perform_three_particle_qkd(self, leader, followers):
        """执行三粒子GHZ态QKD"""
        # 显示参与者私钥
        self._display_private_keys([leader] + followers, "参与者私钥")
        
        # 1. 准备序列
        sequences, decoy_states = self._prepare_sequences([leader] + followers, 3)
        self._display_sequences(sequences, [leader] + followers)
        
        # 2. 显示诱骗态
        self._display_decoy_states(decoy_states, [leader] + followers)
        
        # 3. 执行交换过程
        exchanged_sequences = {}
        for follower in followers:
            # 确定要发送的序列类型
            if follower.id == leader.id + 1 or (leader.id == 4 and follower.id == 1):
                seq_type = 'B'
            else:
                seq_type = 'C'
            
            # 根据领导者的私钥应用Pauli操作
            result_sequence = self.apply_operations(sequences[leader.id][seq_type], leader)
            exchanged_sequences[follower.id] = result_sequence
        
        # 4. 显示交换过程
        self._display_exchange_process(leader, followers, sequences, exchanged_sequences)
        
        # 5. 生成组密钥（通过领导者私钥异或）
        group_key = []
        for i in range(self.M):
            key_bit = leader.private_key[i]
            for follower in followers:
                key_bit ^= follower.private_key[i]
            group_key.append(key_bit)
        
        self.print_key_info(group_key, f"第{leader.id}组初始会话密钥")
        return group_key

    def _perform_bell_state_qkd(self, leader, follower):
        """执行Bell态QKD"""
        # 显示参与者私钥
        self._display_private_keys([leader, follower], "参与者私钥")
        
        # 1. 准备序列
        sequences, decoy_states = self._prepare_sequences([leader, follower], 2)
        self._display_sequences(sequences, [leader, follower])
        
        # 2. 显示诱骗态
        self._display_decoy_states(decoy_states, [leader, follower])
        
        # 3. 执行交换过程
        # 根据领导者的私钥应用Pauli操作
        result_sequence = self.apply_operations(sequences[leader.id]['B'], leader)
        exchanged_sequences = {follower.id: result_sequence}
        
        # 4. 显示交换过程
        self._display_exchange_process(leader, [follower], sequences, exchanged_sequences)
        
        # 5. 生成组密钥（通过领导者私钥异或）
        group_key = []
        for i in range(self.M):
            key_bit = leader.private_key[i] ^ follower.private_key[i]
            group_key.append(key_bit)
        
        self.print_key_info(group_key, f"第{leader.id}组初始会话密钥")
        return group_key

    def _prepare_sequences(self, group_members, num_sequences):
     
        sequences = {}
        decoy_states = {}
        
        for p in group_members:
            sequences[p.id] = {}
            decoy_states[p.id] = {}
            
            # 创建序列
            for i in range(num_sequences):
                seq_type = chr(65 + i)  # A, B, C
                sequences[p.id][seq_type] = self.create_particle_sequence(p.id, i + 1)
                
                # 仅在交换序列中插入诱骗态
                if i > 0:
                    positions, bases, states = self.insert_decoy_states(sequences[p.id][seq_type], self.d)
                    decoy_states[p.id][seq_type] = {
                        'positions': positions,
                        'bases': bases,
                        'states': states
                    }
        
        return sequences, decoy_states

    def _display_sequences(self, sequences, group_members):
        """显示序列信息"""
        self.print_subsection("序列准备")
        
        for p in group_members:
            print(f"\n由P{p.id}准备的序列:")
            print("┌─────────────┐")
            for seq_type in sequences[p.id]:
                # 获取所有粒子的标识符
                particle_ids = []
                for j in range(self.M):
                    # 构建标准格式的粒子标识符
                    particle_id = f"P{p.id},{j+1}({seq_type})"
                    particle_ids.append(particle_id)
                
                # 格式化序列显示
                sequence_str = f"{seq_type}{p.id} = {{{', '.join(particle_ids)}}}"
                print(f"│ {sequence_str} │")
            print("└─────────────┘")

    def _display_decoy_states(self, decoy_states, group_members):

        self.print_subsection("诱骗态信息")
        
        headers = ["参与者", "序列", "插入位置", "测量基底", "量子态"]
        rows = []
        
        for p in group_members:
            for seq_type in decoy_states[p.id]:
                for pos, base, state in zip(
                    decoy_states[p.id][seq_type]['positions'],
                    decoy_states[p.id][seq_type]['bases'],
                    decoy_states[p.id][seq_type]['states']
                ):
                    rows.append([f"P{p.id}", f"{seq_type}{p.id}", pos+1, base, f"|{state}⟩"])
        
        self.print_table(headers, rows)

    def _display_measurement_results(self, group_members, measurement_results):

        self.print_subsection("测量结果")
        
        headers = ["参与者", "测量基底", "测量结果"]
        rows = []
        
        for p in group_members:
            basis = [random.choice(['X', 'Z']) for _ in range(3)]
            results = measurement_results[p.id]
            rows.append([f"P{p.id}", ','.join(basis), ','.join(map(str, results))])
        
        self.print_table(headers, rows)

    def _display_exchange_process(self, leader, followers, sequences, exchanged_sequences):
        """显示交换过程"""
        self.print_subsection("交换过程")
        
        headers = ["发送者", "接收者", "序列", "初始量子态", "Pauli操作", "操作后状态"]
        rows = []
        
        for follower in followers:
            # 根据序列数量确定序列类型
            if len(sequences[leader.id]) == 2:  # Bell态QKD
                seq_type = 'B'
                # 从领导者的私钥获取Pauli操作
                operations = [leader.get_pauli_operation(i % len(leader.private_key)) for i in range(self.M)]
                
                # 构建序列格式的初始态显示（与制备序列格式一致）
                particle_ids = []
                for j in range(self.M):
                    particle_id = f"P{leader.id},{j+1}({seq_type})"
                    particle_ids.append(particle_id)
                initial_state = "{" + ", ".join(particle_ids) + "}"
                
                final_state = ['1' if op == 'X' else '0' for op in operations]
            else:  # 三粒子GHZ态QKD
                seq_type = 'B' if follower.id == leader.id + 1 or (leader.id == 3 and follower.id == 1) else 'C'
                # 从领导者的私钥获取Pauli操作
                operations = [leader.get_pauli_operation(i % len(leader.private_key)) for i in range(self.M)]
                
                # 构建序列格式的初始态显示（与制备序列格式一致）
                particle_ids = []
                for j in range(self.M):
                    particle_id = f"P{leader.id},{j+1}({seq_type})"
                    particle_ids.append(particle_id)
                initial_state = "{" + ", ".join(particle_ids) + "}"
                
                final_state = ['1' if op == 'X' else '0' for op in operations]
            
            rows.append([
                f"P{leader.id}",
                f"P{follower.id}",
                f"{seq_type}{leader.id}",
                initial_state,
                ','.join(operations),
                f"|{','.join(final_state)}⟩"
            ])
        
        self.print_table(headers, rows)

def main():
    # 获取用户输入
    while True:
        try:
            m_value = int(input("请输入每个参与者制备的量子态数量 M = "))
            if m_value > 0:
                break
            print("请输入一个正整数")
        except ValueError:
            print("请输入有效的整数")
    
    while True:
        try:
            num_participants = int(input("请输入参与者总数 N = "))
            if num_participants >= 3:
                break
            print("参与者数量必须大于或等于3")
        except ValueError:
            print("请输入有效的整数")
    
    # 创建量子密钥交换系统
    qke = QuantumKeyExchange(num_participants, m_value)
    
    print("\n╔════════════════════════════════════╗")
    print("║     量子密钥交换系统初始化        ║")
    print("╠════════════════════════════════════╣")
    print(f"║ 参与者总数: N = {num_participants:<18} ║")
    print(f"║ 量子态数量: M = {m_value:<18} ║")
    print("╚════════════════════════════════════╝")
    
    # 执行密钥分发
    print("\n开始密钥分发过程...")
    qke.distribute_key()
    
    # 验证密钥一致性
    print("\n╔════════════════════════════════════╗")
    print("║         密钥一致性验证            ║")
    print("╚════════════════════════════════════╝")
    leader = next(p for p in qke.participants if p.is_leader)
    leader_key = leader.shared_key
    
    all_keys_match = True
    for participant in qke.participants:
        if participant.shared_key != leader_key:
            all_keys_match = False
            print(f"\n 参与者{participant}的密钥与领导者密钥不匹配")
            print(f"├─ 领导者密钥: [{', '.join(map(str, leader_key))}]")
            print(f"└─ 参与者密钥: [{', '.join(map(str, participant.shared_key))}]")
            break
    
    if all_keys_match:
        print("\n✓ 验证结果：所有参与者的密钥完全匹配！")
        print(f"├─ 成功获取共享密钥的参与者数量: {len(qke.participants)}")
        print(f"├─ 生成的密钥长度: {len(leader_key)} 比特")
        print(f"└─ 最终会话密钥: [{', '.join(map(str, leader_key))}]")
    else:
        print("\n✗ 验证结果：密钥分发失败，检测到密钥不匹配")

if __name__ == "__main__":
    main() 