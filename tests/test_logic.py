from common.tables import Word2Vec
from logic import VectorLogic
from mocks.hs_test_case import HsTestCase
from mocks.mock_db import MockDb
from fakeredis import FakeRedis


class TestVectorLogic(HsTestCase):
    def setUp(self) -> None:
        self.db = MockDb()
        self.redis = FakeRedis()
        self.shalom_raw_vec = b"\xdd\xba\xd7\xbd,\xa6\x8d=4\xf0>\xbe\x1b\xcd\xf7\xbd!\xd1\x9b\xbd\xef\x88\x96\xbd[\x1f\xc2=\xbf\xde\xf0<\xe2\x15\x04>\t\xc3\xe0\xbc\x91y\xba=$\x1a/\xbe\xe8\xf3\x0e\xbeWa\x16>\xbf\x84\xf7\xbc\xa8\x8b\xee\xbd<\xc2.>\x91n\xa9\xbd\xf9}a=;\x1d\x17\xbd\xfb\xd0b=F(\x89;\xb3\x7f}=\xe0QR=\xaa\xdc%\xbd\xa7:\x7f\xbdM\xad,\xbdoO[=\x11\xb3\xc5:\x93\x83\x16\xbd\x19\xc0\x12\xbdv\x9fC\xbdV?|=\x93[\xf2\xbd\xb6\xa8\x16\xbcf\xfc\xc9<3\xb5\xd8=^3\x87\xbe}x\x8e\xbcx4\xcb\xbc\x04\xd6f>=\xdc\xec\xbd\xf1\x98A\xbd{\x82\xe6<\x1b\xac\x0e\xbdh\x82\x1b\xbd\xd5P\xef=\xa5\x02U\xbd@5\xf4=\xc21\x99=O \x15\xbd\xb86\xa8\xb98\xb6+>\x84\nO\xbd7)\x8b<_\xffI\xbd\x80+\x01>U\xf0==\x80\xb5\x9d=;\xd2\xe1<\xbd\x0c\x02=&jU<@\x90\x01>%n\x98<-\xc7\xe3;q|$>\\\xb4\x0b='\xa5.>.Y\xc5\xbc\xa0\xf8\x11\xbe\xe2[\x10=s\x00\xa3=\xeb\x0e\x82;\x84@\xba=\x15\xa1\xcb=\xa1\xff'=\x1b\xf7D>g\xc4\x92\xbd\xccfv>\xa0K\xb8\xbcn\xe6^\xbe\x1e\x92\x12>k\x94+\xbdHz8\xbd\x01\x0fM=r\xd4\x05\xbe\x9e\xbcW>:U\x91=\x87\xd6\x84=\xc6_\x97=\xaf['>j\x96\x06\xbdc\xd1\xe4=\x81\xfd\xcc\xbd\\\xdf\x1e>j\x8ez=\x9c\xbd\xa2=s#\xea=2\xbc\x05\xbc\x02\xad5="
        self.shalom_vec = (-0.10533688217401505, 0.06916460394859314, -0.18646317720413208, -0.12099667638540268, -0.07608247548341751, -0.07350336760282516, 0.09478636831045151, 0.029403088614344597, 0.12898972630500793, -0.027436750009655952, 0.09105218201875687, -0.17099815607070923, -0.13960230350494385, 0.1468556970357895, -0.030214665457606316, -0.11647731065750122, 0.17066282033920288, -0.08273041993379593, 0.0550517775118351, -0.03689311072230339, 0.055375080555677414, 0.004185709170997143, 0.06188936159014702, 0.05134761333465576, -0.040493644773960114, -0.062311794608831406, -0.04215746000409126, 0.05354255065321922, 0.0015083273174241185, -0.03674657270312309, -0.03582772985100746, -0.04775949567556381, 0.06158383935689926, -0.11833872646093369, -0.009195497259497643, 0.02465648576617241, 0.1058143600821495, -0.2640637755393982, -0.01739143766462803, -0.02480529248714447, 0.22542577981948853, -0.11565444618463516, -0.04726499691605568, 0.02813838981091976, -0.034832101315259933, -0.03796616196632385, 0.11685339361429214, -0.05200447514653206, 0.11924219131469727, 0.07480193674564362, -0.03640776500105858, -0.0003208422567695379, 0.1676872968673706, -0.05054713785648346, 0.016987426206469536, -0.04931580647826195, 0.1261425018310547, 0.04637177661061287, 0.07700634002685547, 0.02756606601178646, 0.031750429421663284, 0.013025796040892601, 0.1265268325805664, 0.018607208505272865, 0.006951233837753534, 0.1606309562921524, 0.034107550978660583, 0.17055188119411469, -0.024090375751256943, -0.14254999160766602, 0.03524387627840042, 0.07959070056676865, 0.003969063516706228, 0.0909433662891388, 0.09942833334207535, 0.041015271097421646, 0.1923488825559616, -0.07166367024183273, 0.2406265139579773, -0.02249699831008911, -0.21767589449882507, 0.14313551783561707, -0.04188958927989006, -0.04503849148750305, 0.05006313696503639, -0.1306932270526886, 0.21068045496940613, 0.07096333801746368, 0.06486230343580246, 0.07391314208507538, 0.1634356826543808, -0.032858289778232574, 0.11172749847173691, -0.10009289532899857, 0.1551489233970642, 0.061170972883701324, 0.07946321368217468, 0.11432542651891708, -0.008162545040249825, 0.04435444623231888)
        self.another_raw_vec = b'_\x89\x89=n\xf9\xa4\xbdRH\x15\xbc\x1a*\x96<:]\x90\xbd\xd4\xde\x15\xbe\x14k\xac=\xc5\xce7>\x97\n\x97\xbd\x08\xce\x98\xbdk\xb0\xa1<gh7\xbe\xb0_\xc1<\xf4\xbf\x18\xbd\xc0p\xfd\xbc\xf5\xe9\x02\xbe.s\xa3=x3a\xbe\xfa\xa5\x08\xbd4t\x81<#\xb3\x11=\x9f\xb8\xc5\xbcs\xec\xc8<*\xd1(>\xca\xc4\xda\xbd(\xccM>\x8bz\x17\xbe\xe9\xa4(\xbd\x1a\x99m\xbep0\x05\xbe\x9c\x07]=\xb1m\x0b=[\xd1M\xbd\x87\x12\x86\xbd\xf7\x9a\xdd<\x1c\x80I=\xa1\xa0r<\xef{\x86=\x08\xe3\xab=t>\xce\xbd\xc5\xb4y;\xccu\xb5\xbd\x89+\xa0=\x08\xf0a>\x8b\xdc3\xbd\xffV7=|\x1f\xb5\xbd\xb1\xb1-=J\xb2\x13<\xff\x84\x87>v\xb8\xb8\xbd\x8d\xd3M=\xb8F!\xbdd|\x1e\xbe\xa0se\xbc"\xfc\xe6=W\xdd\x8d=YP\xe9\xbdG\xefo\xbc\xcc~\xe4<\x08M\xbd=\xbcf\xe3<\xf6\xbc\x98<\xfa\xa2s=\xcd\xcf\xae\xbd#N\t=J\x1e\x89>c\x11\x18>\xe0\xa8\x19\xbe%\xbf\x91=s\x92\x8b=\x86\xc0z\xbd\xe0\x1b\x1f>\x90\xf3<=\xff\x8b\xec=\x14j7=@\xcc\x1a\xbd9^\'=Uc\x11>\xc6\x98\x02=y\x03\xdb=\x9f\xca=>h\x10\x08\xbe\xb0\x95\x99\xbcU`\x8f;8\xbe\xa5\xbc6\xb4\x87\xbdB\x1eh\xbdw\xdd9\xba\x1e;\x8f=\x04\xb1\xcf<\xa7\xdb\xf7<m\x8d(\xbc\xe8\xe8h\xba&/\xe7=\xb31\xd3=[\xae\xd1<\xf6\x97\x06>\xa4Bj\xbd"\xf5G\xbe'
        self.m_SecretLogic = self.patch('logic.SecretLogic')
        self.m_secret_logic = self.m_SecretLogic.return_value
        self.testee = VectorLogic(self.db.session_factory, self.redis)

    def test_get_vector(self):
        # arrange
        self.db.add(Word2Vec(word='שלום', vec=self.shalom_raw_vec))

        # act
        vector = self.testee.get_vector('שלום')

        # assert
        self.assertEqual(self.shalom_vec, vector)

    def test_get_vector__no_such_word(self):
        # act
        vector = self.testee.get_vector('שלום')

        # assert
        self.assertIsNone(vector)

    def test_get_similarity__the_same(self):
        # arrange
        self.db.add(Word2Vec(word='שלום', vec=self.shalom_raw_vec))
        self.m_secret_logic.get_secret.return_value = 'שלום'

        # act
        similarity = self.testee.get_similarity('שלום')

        # assert
        self.m_SecretLogic.assert_called_once_with(self.db.session_factory, self.redis)
        self.m_secret_logic.get_secret.assert_called_once_with()
        self.assertEqual(100, similarity)

    def test_get_similarity__not_the_same(self):
        # arrange
        self.db.add(Word2Vec(word='שלום', vec=self.shalom_raw_vec))
        self.db.add(Word2Vec(word='שלשל', vec=self.another_raw_vec))
        self.m_secret_logic.get_secret.return_value = 'שלשל'

        # act
        similarity = self.testee.get_similarity('שלום')

        # assert
        self.m_SecretLogic.assert_called_once_with(self.db.session_factory, self.redis)
        self.m_secret_logic.get_secret.assert_called_once_with()
        self.assertLess(similarity, 100)
        self.assertGreater(similarity, 0)

    def test_get_similarity__no_such_word(self):
        # arrange
        self.db.add(Word2Vec(word='שלשל', vec=self.another_raw_vec))
        self.m_secret_logic.get_secret.return_value = 'שלשל'

        # act
        similarity = self.testee.get_similarity('שלום')

        # assert
        self.m_secret_logic.get_secret.assert_not_called()
        self.assertEqual(similarity, -1)
